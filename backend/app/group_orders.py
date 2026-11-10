"""Staff-group order notifications — pure, testable logic.

Shared by:
  * the FastAPI process (app/notify.py posts/edits the group message over
    plain HTTP), and
  * the bot process (app/bot.py handles staff button taps via callbacks).

Nothing in here touches Telegram, HTTP or the database — builders take an
order (ORM object or plain dict) and return plain data, and the transition
validator is a pure function of (current_status, target_status).
"""
from datetime import datetime

# Forward flow, in order. "cancelled" sits outside this chain.
STEPS = ["placed", "accepted", "preparing", "ready", "completed"]
ALL_STATUSES = STEPS + ["cancelled"]
TERMINAL = ("completed", "cancelled")

STEP_LABELS = {
    "placed": "Order Placed",
    "accepted": "Accepted",
    "preparing": "Preparing",
    "ready": "Ready for Pickup",
    "completed": "Completed",
    "cancelled": "Cancelled",
}
STEP_EMOJI = {
    "placed": "🧾",
    "accepted": "👍",
    "preparing": "👨‍🍳",
    "ready": "🔔",
    "completed": "✅",
    "cancelled": "🚫",
}


def callback_data(order_code, status):
    """Inline-button payload, e.g. 'ord:BB1A2B3C4D:accepted'."""
    return f"ord:{order_code}:{status}"


def parse_callback(data):
    """'ord:<code>:<status>' -> (code, status) or (None, None)."""
    if not data:
        return None, None
    parts = str(data).split(":")
    if len(parts) != 3 or parts[0] != "ord" or parts[2] not in ALL_STATUSES:
        return None, None
    return parts[1], parts[2]


def validate_transition(current, target):
    """Return (allowed: bool, reason: str).

    reason is one of: "ok", "invalid" (unknown status), "noop" (target ==
    current), "terminal" (current is completed/cancelled), "backward"
    (target step is behind current; cancelled never counts as backward —
    it is allowed from any non-final state).
    """
    if current not in ALL_STATUSES or target not in ALL_STATUSES:
        return False, "invalid"
    if target == current:
        return False, "noop"
    if current in TERMINAL:
        return False, "terminal"
    if target == "cancelled":
        return True, "ok"
    if current == "cancelled":  # unreachable (terminal above), kept explicit
        return False, "terminal"
    if STEPS.index(target) > STEPS.index(current):
        return True, "ok"
    return False, "backward"


def can_transition(current, target):
    return validate_transition(current, target)[0]


def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _money(v):
    try:
        return f"₹{float(v):,.2f}"
    except (TypeError, ValueError):
        return f"₹{v}"


def _fmt_time(dt):
    if dt is None:
        return ""
    if isinstance(dt, str):
        return dt
    try:
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(dt)


def _addon_names(addons):
    names = []
    for a in addons or []:
        if isinstance(a, dict):
            if a.get("name"):
                names.append(str(a["name"]))
        elif a:
            names.append(str(a))
    return names


def build_message_text(order, updated_by=None, updated_at=None):
    """Full group-message text for an order (ORM object or dict)."""
    code = _get(order, "order_code", "")
    status = _get(order, "status", "placed")
    label = STEP_LABELS.get(status, status)
    emoji = STEP_EMOJI.get(status, "🧾")
    lines = [f"🛎️ Order {code}", f"Status: {emoji} {label}", "", "🍽️ Items:"]
    items = _get(order, "items", []) or []
    if not items:
        lines.append("• (no items)")
    for it in items:
        qty = _get(it, "quantity", 1)
        name = _get(it, "name", "Item")
        size = _get(it, "size", "")
        addons = _addon_names(_get(it, "addons", []))
        line_total = _get(it, "line_total", None)
        desc = f"• {qty} × {name}"
        extras = []
        if size:
            extras.append(size)
        extras.extend(addons)
        if extras:
            desc += " (" + ", ".join(extras) + ")"
        if line_total is not None:
            desc += f" — {_money(line_total)}"
        lines.append(desc)
        note = _get(it, "instructions", "")
        if note:
            lines.append(f"   ↳ {note}")
    lines.append("")
    lines.append(f"Subtotal: {_money(_get(order, 'subtotal', 0))}")
    discount = _get(order, "discount", 0) or 0
    if discount:
        coupon = _get(order, "coupon_code", "")
        suffix = f" ({coupon})" if coupon else ""
        lines.append(f"Discount{suffix}: −{_money(discount)}")
    lines.append(f"GST: {_money(_get(order, 'gst_amount', 0))}")
    lines.append(f"Total: {_money(_get(order, 'total', 0))}")
    lines.append("")
    cust = _get(order, "customer_name", "") or "Guest"
    phone = _get(order, "phone", "")
    lines.append(f"👤 Customer: {cust}" + (f" • {phone}" if phone else ""))
    otype = _get(order, "order_type", "takeaway")
    if otype == "dine-in":
        table = _get(order, "table_number", "")
        lines.append(f"📍 Dine-in" + (f" • Table {table}" if table else ""))
    else:
        lines.append("📍 Takeaway")
    pay_method = _get(order, "payment_method", "cash")
    pay_status = _get(order, "payment_status", "")
    lines.append(f"💳 Payment: {pay_method}" + (f" ({pay_status})" if pay_status else ""))
    placed = _fmt_time(_get(order, "created_at", None))
    eta = _get(order, "eta_mins", 25)
    tail = f"🕐 Placed: {placed}" if placed else "🕐 Placed"
    if eta:
        tail += f" • ETA ~{eta} mins"
    lines.append(tail)
    instructions = _get(order, "instructions", "")
    if instructions:
        lines.append(f"📝 Note: {instructions}")
    if updated_by:
        when = _fmt_time(updated_at) if updated_at else _fmt_time(datetime.utcnow())
        lines.append("")
        lines.append(f"Last updated by {updated_by} • {when}")
    return "\n".join(lines)


def build_keyboard(order_code, current_status):
    """Inline keyboard as plain data: rows of {text, callback_data} dicts.

    Markers: ✅ steps already passed, 🔵 current step, plain = upcoming.
    A Cancel Order row is shown for every non-terminal status. For a
    cancelled order the step rows stay plain and a single 🚫 row replaces
    the cancel row. Every button keeps a valid callback_data so taps on
    passed/current steps can be answered with a notice by the bot.
    """
    def btn(status, text):
        return {"text": text, "callback_data": callback_data(order_code, status)}

    if current_status == "cancelled":
        rows = []
        plain = [btn(s, STEP_LABELS[s]) for s in STEPS]
        rows.append(plain[0:2])
        rows.append(plain[2:4])
        rows.append(plain[4:5])
        rows.append([btn("cancelled", "🚫 Cancelled")])
        return rows

    cur = STEPS.index(current_status) if current_status in STEPS else 0
    rendered = []
    for i, s in enumerate(STEPS):
        if i < cur:
            text = f"✅ {STEP_LABELS[s]}"
        elif i == cur:
            text = f"🔵 {STEP_LABELS[s]}"
        else:
            text = STEP_LABELS[s]
        rendered.append(btn(s, text))
    rows = [rendered[0:2], rendered[2:4], rendered[4:5]]
    if current_status not in TERMINAL:
        rows.append([btn("cancelled", "❌ Cancel Order")])
    return rows
