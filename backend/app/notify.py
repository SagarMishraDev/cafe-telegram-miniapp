"""Telegram staff-group notifications from the FastAPI process.

Plain httpx calls to api.telegram.org, so order placement can post the
staff-group message without depending on the bot process running.

Best-effort by design: every function swallows its own errors (logging a
warning) — an unreachable/unconfigured Telegram must NEVER break or roll
back an order. GROUP_CHAT_ID empty -> skip silently.
"""
import logging

import httpx

from .config import settings
from .group_orders import build_keyboard, build_message_text

log = logging.getLogger(__name__)
API_BASE = "https://api.telegram.org"
TIMEOUT = 10.0


def _chat_id():
    raw = (settings.GROUP_CHAT_ID or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return raw  # e.g. a @channelusername-style id


def is_configured():
    return bool(settings.BOT_TOKEN) and _chat_id() is not None


def _url(method):
    return f"{API_BASE}/bot{settings.BOT_TOKEN}/{method}"


def _markup(order):
    return {"inline_keyboard": build_keyboard(order.order_code, order.status)}


def send_group_order(order):
    """Post the order message to the staff group.

    Returns the Telegram message_id (int) on success, else None.
    """
    if not settings.BOT_TOKEN:
        log.info("notify: BOT_TOKEN not set — skipping group notification")
        return None
    chat_id = _chat_id()
    if chat_id is None:
        log.info("notify: GROUP_CHAT_ID not set — skipping group notification")
        return None
    try:
        resp = httpx.post(
            _url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": build_message_text(order),
                "reply_markup": _markup(order),
            },
            timeout=TIMEOUT,
        )
        data = resp.json()
        if not data.get("ok"):
            log.warning(f"notify: sendMessage rejected: {data.get('description')}")
            return None
        return data["result"]["message_id"]
    except Exception as e:
        log.warning(f"notify: group notification failed (order still placed): {e}")
        return None


def edit_group_order(order, updated_by=None):
    """Sync the stored group message after a status change (e.g. from the
    admin dashboard). Returns True if Telegram confirmed the edit."""
    if not settings.BOT_TOKEN:
        return False
    chat_id = _chat_id()
    message_id = getattr(order, "group_message_id", None)
    if chat_id is None or not message_id:
        return False
    try:
        resp = httpx.post(
            _url("editMessageText"),
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": build_message_text(order, updated_by=updated_by),
                "reply_markup": _markup(order),
            },
            timeout=TIMEOUT,
        )
        data = resp.json()
        if not data.get("ok"):
            desc = data.get("description", "")
            if "message is not modified" in desc:
                log.info("notify: group message already up to date")
            else:
                log.warning(f"notify: editMessageText rejected: {desc}")
            return False
        return True
    except Exception as e:
        log.warning(f"notify: group message edit failed: {e}")
        return False
