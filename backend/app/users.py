"""Race-safe user get-or-create.

Concurrent auth calls (multiple Mini App instances, React double effects)
can both find no user and both INSERT — the second commit then dies with
``UNIQUE constraint failed: users.telegram_id`` and the request 500s.
This helper treats that IntegrityError as "the other request won": roll
back, re-query, and return the row it created.
"""
from sqlalchemy.exc import IntegrityError
from .models import User


def get_or_create_user(db, telegram_id, username="", first_name="", last_name=""):
    tid = str(telegram_id)
    user = db.query(User).filter(User.telegram_id == tid).first()
    if user:
        return user
    user = User(telegram_id=tid, username=username or "", first_name=first_name or "", last_name=last_name or "")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Another concurrent request inserted the same telegram_id first.
        db.rollback()
        existing = db.query(User).filter(User.telegram_id == tid).first()
        if existing:
            return existing
        raise
    db.refresh(user)
    return user
