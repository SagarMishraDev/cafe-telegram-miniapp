"""Regression tests for the auth 500 crash (Sagar's live log, 2026-11-11):
concurrent POST /api/auth/telegram calls raced the user get-or-create —
both found no row, both INSERTed, the second died with
``UNIQUE constraint failed: users.telegram_id`` -> 500.

The race is simulated deterministically: the first user lookup in the
request is made to lie (return None) while the row actually exists, which
is exactly what the losing request saw. Auth must return 200 with the
existing user's id, never 500.

Reuses the test harness (isolated DB + seeded client) from test_api.py.
Sandbox note: proxy env vars must be unset when running this suite
(python-telegram-bot Application builds happen in test_group_orders.py).
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import test_api  # noqa: E402  (sets up test DB, seed, TestClient)
client = test_api.client

import app.database as dbmod  # noqa: E402
from app.models import User  # noqa: E402
from app.users import get_or_create_user  # noqa: E402
from app.config import settings  # noqa: E402
from app.security import make_init_data  # noqa: E402
from sqlalchemy.orm import Session as _Session  # noqa: E402

TEST_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


# --- lie-once query shim: first .first() pretends the row does not exist ---
class _LieQuery:
    def __init__(self, real, state):
        self._real = real
        self._state = state

    def filter(self, *a, **k):
        return _LieQuery(self._real.filter(*a, **k), self._state)

    def order_by(self, *a, **k):
        return _LieQuery(self._real.order_by(*a, **k), self._state)

    def first(self):
        if not self._state["lied"]:
            self._state["lied"] = True
            return None
        return self._real.first()

    def __getattr__(self, name):
        return getattr(self._real, name)


def _install_lie_once(monkeypatch):
    state = {"lied": False}
    orig_query = _Session.query

    def lie_query(self, *entities, **kw):
        return _LieQuery(orig_query(self, *entities, **kw), state)

    monkeypatch.setattr(_Session, "query", lie_query)
    return state


def _get_or_create_row(tid, **kw):
    db = dbmod.SessionLocal()
    try:
        u = db.query(User).filter(User.telegram_id == str(tid)).first()
        if not u:
            u = User(telegram_id=str(tid), **kw)
            db.add(u)
            db.commit()
            db.refresh(u)
        return u.id
    finally:
        db.close()


# --- helper-level: the losing racer must get the winner's row --------------
def test_get_or_create_user_survives_insert_race(monkeypatch):
    uid = _get_or_create_row("race-1", username="racer", first_name="Race")
    _install_lie_once(monkeypatch)
    db = dbmod.SessionLocal()
    try:
        user = get_or_create_user(db, "race-1", username="racer", first_name="Race")
        assert user.id == uid
    finally:
        db.close()


# --- endpoint, dev path: repeated + raced auth must not 500 -----------------
def test_dev_auth_race_no_500(monkeypatch):
    r1 = client.post("/api/auth/telegram", json={"initData": ""})
    assert r1.status_code == 200, r1.text
    uid = r1.json()["user"]["id"]
    _install_lie_once(monkeypatch)
    r2 = client.post("/api/auth/telegram", json={"initData": ""})
    assert r2.status_code == 200, r2.text
    assert r2.json()["user"]["id"] == uid


# --- endpoint, real Telegram path: raced first-login must not 500 -----------
def test_telegram_auth_race_no_500(monkeypatch):
    uid = _get_or_create_row("777001", username="tg_racer", first_name="Tg")
    data = make_init_data({"id": 777001, "first_name": "Tg", "username": "tg_racer"}, TEST_TOKEN)
    monkeypatch.setattr(settings, "BOT_TOKEN", TEST_TOKEN)
    _install_lie_once(monkeypatch)
    r = client.post("/api/auth/telegram", json={"initData": data})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["id"] == uid
    # And a normal (non-raced) repeat login still works and reuses the row.
    r2 = client.post("/api/auth/telegram", json={"initData": data})
    assert r2.status_code == 200, r2.text
    assert r2.json()["user"]["id"] == uid
