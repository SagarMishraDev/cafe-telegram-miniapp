"""Tests for the staff-group order notification feature:
transition validator, keyboard builder, message text builder,
notify.py skip/failure behaviour, and the bot's DB status-change helper.
Reuses the test harness (isolated DB + seeded client) from test_api.py.
"""
import os, sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import test_api  # noqa: E402  (sets up test DB, seed, TestClient)
client = test_api.client

from app.group_orders import (  # noqa: E402
    build_keyboard, build_message_text, can_transition, callback_data,
    parse_callback, validate_transition,
)
from app.config import settings  # noqa: E402
import app.notify as notify  # noqa: E402
import httpx  # noqa: E402


# --- transition validator -------------------------------------------------
def test_transitions_forward_ok():
    assert can_transition("placed", "accepted")
    assert can_transition("accepted", "preparing")
    assert can_transition("preparing", "ready")
    assert can_transition("ready", "completed")
    assert can_transition("placed", "preparing")  # forward jump is still forward
    assert validate_transition("placed", "accepted") == (True, "ok")

def test_transitions_backward_rejected():
    assert not can_transition("preparing", "accepted")
    assert validate_transition("preparing", "accepted") == (False, "backward")
    assert validate_transition("completed", "placed") == (False, "terminal")

def test_transitions_noop_and_invalid():
    assert validate_transition("accepted", "accepted") == (False, "noop")
    assert validate_transition("placed", "bogus") == (False, "invalid")
    assert validate_transition("bogus", "accepted") == (False, "invalid")

def test_transitions_cancel_rules():
    for s in ("placed", "accepted", "preparing", "ready"):
        assert can_transition(s, "cancelled"), s
    assert validate_transition("completed", "cancelled") == (False, "terminal")
    assert validate_transition("cancelled", "accepted") == (False, "terminal")
    assert validate_transition("cancelled", "cancelled") == (False, "noop")


# --- keyboard builder -------------------------------------------------------
def _flat(rows):
    return [b for row in rows for b in row]

def test_keyboard_markers_mid_flow():
    rows = build_keyboard("BBTEST1234", "preparing")
    flat = _flat(rows)
    by_status = {}
    for b in flat:
        code, status = parse_callback(b["callback_data"])
        assert code == "BBTEST1234"
        by_status[status] = b["text"]
    assert by_status["placed"].startswith("✅")
    assert by_status["accepted"].startswith("✅")
    assert by_status["preparing"].startswith("🔵")
    assert by_status["ready"] == "Ready for Pickup"       # upcoming: plain
    assert by_status["completed"] == "Completed"          # upcoming: plain
    assert "Cancel" in by_status["cancelled"]             # cancel row present

def test_keyboard_completed_has_no_cancel_and_cancelled_state():
    rows = build_keyboard("BBX", "completed")
    flat = _flat(rows)
    assert all(parse_callback(b["callback_data"])[1] != "cancelled" for b in flat)
    texts = {parse_callback(b["callback_data"])[1]: b["text"] for b in flat}
    assert texts["completed"].startswith("🔵")
    assert texts["ready"].startswith("✅")
    rows_c = build_keyboard("BBX", "cancelled")
    assert "Cancelled" in _flat(rows_c)[-1]["text"]

def test_callback_data_format_roundtrip():
    assert callback_data("BB1", "accepted") == "ord:BB1:accepted"
    assert parse_callback("ord:BB1:accepted") == ("BB1", "accepted")
    assert parse_callback("ord:BB1:bogus") == (None, None)
    assert parse_callback("junk") == (None, None)
    assert parse_callback("") == (None, None)


# --- message text builder ---------------------------------------------------
def _fake_order(**over):
    base = dict(
        order_code="BBFAKE001", status="placed", customer_name="Sagar",
        phone="9876543210", order_type="dine-in", table_number="4",
        payment_method="upi", payment_status="paid",
        subtotal=987.0, discount=98.7, gst_amount=44.42, total=932.72,
        coupon_code="WELCOME10", eta_mins=25, instructions="Less spicy please",
        created_at=None,
        items=[SimpleNamespace(name="Farmhouse Burger", quantity=2, size="Large",
                               addons=[{"name": "Extra Cheese", "price": 40}],
                               instructions="", line_total=838.0),
               SimpleNamespace(name="Cold Coffee", quantity=1, size="",
                               addons=[], instructions="", line_total=149.0)],
    )
    base.update(over)
    return SimpleNamespace(**base)

def test_message_text_contents():
    txt = build_message_text(_fake_order())
    assert "BBFAKE001" in txt
    assert "Farmhouse Burger" in txt and "Extra Cheese" in txt and "Large" in txt
    assert "Cold Coffee" in txt
    assert "₹932.72" in txt                      # total
    assert "Table 4" in txt                       # dine-in table
    assert "9876543210" in txt and "Sagar" in txt  # phone + customer
    assert "Order Placed" in txt                  # status label
    txt2 = build_message_text(_fake_order(order_type="takeaway", table_number=""))
    assert "Takeaway" in txt2

def test_message_text_accepts_dict_and_updated_by():
    d = {"order_code": "BBDICT01", "status": "accepted", "customer_name": "Asha",
         "phone": "9000000000", "order_type": "takeaway", "payment_method": "cash",
         "payment_status": "pay_at_cafe", "subtotal": 200, "discount": 0,
         "gst_amount": 10, "total": 210, "items": [{"name": "Momos", "quantity": 1,
         "size": "", "addons": [], "line_total": 200}]}
    txt = build_message_text(d, updated_by="Rahul")
    assert "BBDICT01" in txt and "Momos" in txt and "Accepted" in txt
    assert "Last updated by Rahul" in txt


# --- notify.py behaviour ------------------------------------------------------
class _Resp:
    def __init__(self, payload): self._p = payload
    def json(self): return self._p

def test_notify_skips_when_group_unset(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "123:abc")
    monkeypatch.setattr(settings, "GROUP_CHAT_ID", "")
    def boom(*a, **k): raise AssertionError("httpx.post must not be called")
    monkeypatch.setattr(httpx, "post", boom)
    assert notify.send_group_order(_fake_order()) is None
    assert notify.edit_group_order(_fake_order(group_message_id=5)) is False

def test_notify_success_returns_message_id(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "123:abc")
    monkeypatch.setattr(settings, "GROUP_CHAT_ID", "-1001234567890")
    seen = {}
    def fake_post(url, json=None, timeout=None):
        seen["url"] = url; seen["json"] = json
        return _Resp({"ok": True, "result": {"message_id": 4242}})
    monkeypatch.setattr(httpx, "post", fake_post)
    mid = notify.send_group_order(_fake_order())
    assert mid == 4242
    assert seen["json"]["chat_id"] == -1001234567890
    kb = seen["json"]["reply_markup"]["inline_keyboard"]
    assert parse_callback(kb[0][0]["callback_data"]) == ("BBFAKE001", "placed")

def test_notify_failure_is_swallowed(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "123:abc")
    monkeypatch.setattr(settings, "GROUP_CHAT_ID", "-1001")
    def down(*a, **k): raise httpx.ConnectError("no network")
    monkeypatch.setattr(httpx, "post", down)
    assert notify.send_group_order(_fake_order()) is None

def test_order_creation_survives_telegram_failure(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "123:abc")
    monkeypatch.setattr(settings, "GROUP_CHAT_ID", "-1001")
    def down(*a, **k): raise httpx.ConnectError("telegram down")
    monkeypatch.setattr(httpx, "post", down)
    menu = client.get("/api/menu").json()
    r = client.post("/api/orders", json={"customer_name": "T", "phone": "9000000000",
                    "order_type": "takeaway", "payment_method": "cash",
                    "items": [{"food_item_id": menu[0]["id"], "quantity": 1}]})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "placed"


# --- bot DB helper (shared-database status changes) ---------------------------
def test_bot_status_change_helper():
    import app.bot as bot
    menu = client.get("/api/menu").json()
    r = client.post("/api/orders", json={"customer_name": "Helper", "phone": "9000000001",
                    "order_type": "takeaway", "payment_method": "cash",
                    "items": [{"food_item_id": menu[0]["id"], "quantity": 1}]})
    assert r.status_code == 200, r.text
    code = r.json()["order_code"]
    res = bot._apply_status_change(code, "accepted", "Test Staff")
    assert res["result"] == "ok" and res["status"] == "accepted"
    assert "Last updated by Test Staff" in res["text"]
    # backward tap changes nothing
    res2 = bot._apply_status_change(code, "placed", "Test Staff")
    assert res2["result"] == "backward"
    # same-step tap is a noop
    res3 = bot._apply_status_change(code, "accepted", "Test Staff")
    assert res3["result"] == "noop"
    # cancel from a non-final state works, then everything is terminal
    res4 = bot._apply_status_change(code, "cancelled", "Test Staff")
    assert res4["result"] == "ok"
    res5 = bot._apply_status_change(code, "preparing", "Test Staff")
    assert res5["result"] == "terminal"
    assert bot._apply_status_change("BBNOPE404", "accepted", "T")["result"] == "not_found"
    # DB really changed (visible through the API the customer tracker polls)
    mine = client.get("/api/orders/my").json()
    mine_by_code = {o["order_code"]: o for o in mine}
    assert mine_by_code[code]["status"] == "cancelled"
