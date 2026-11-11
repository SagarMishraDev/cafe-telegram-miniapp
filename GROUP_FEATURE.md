# Staff Group Order Notifications — Feature Notes
Added: 10 Nov 2026 • Status: built + tested (see results below)

## What it does
When a customer places an order in the Mini App, the backend posts a message to the cafe's **staff Telegram group** with the complete order — code, items with quantity/size/add-ons/notes, subtotal/discount/GST/total, customer name + phone, dine-in table or takeaway, payment method + status, placed time and ETA — and **inline status buttons**:

`✅ Order Placed` → `Accepted` → `Preparing` → `Ready for Pickup` → `Completed`, plus `❌ Cancel Order`.

- Passed steps show ✅, the current step shows 🔵, upcoming steps are plain.
- Staff tap buttons **in the group** — no admin dashboard needed. A valid tap updates the order in the same database the API uses, edits the group message (new state + who updated it + time), and DMs the customer their status update on the bot. The customer's Mini App tracker (already polls the API) moves at the same time, and admin-dashboard status changes also edit the group message to stay in sync.
- Rules: forward steps only; Cancel allowed from any non-final state; completed/cancelled are terminal; tapping a passed or current step just shows a notice and changes nothing.

## How it is wired
| Piece | File |
|---|---|
| Pure logic — transition validator, keyboard builder, message-text builder, callback parse/format | `backend/app/group_orders.py` (new) |
| API-side Telegram calls (plain httpx, best-effort, never blocks/fails an order) | `backend/app/notify.py` (new) |
| Order creation hook — posts group message, stores `group_message_id` | `backend/app/routers/orders.py` |
| Admin status-change hook — edits the group message | `backend/app/routers/admin.py` |
| Bot callbacks (`ord:<code>:<status>`), `/chatid` setup helper, customer DMs | `backend/app/bot.py` |
| `GROUP_CHAT_ID` setting + `orders.group_message_id` column (+ startup auto-add for older local DBs) | `backend/app/config.py`, `backend/app/models.py`, `backend/app/main.py` |

Config notes: the **API process** reads `GROUP_CHAT_ID` from `backend/.env` (pydantic settings). The **bot process** now reads `BOT_TOKEN`/`WEBAPP_URL` from the same `backend/.env` (via `app.config`) — no per-terminal `$env:` line needed; a terminal value still wins if set. It does **not** need `GROUP_CHAT_ID`: button taps arrive as callback queries with the group message attached.

## Setup (also in README)
1. Create a staff Telegram group, add **@Digital_Cafebot**.
2. Send `/chatid` in the group — bot replies with the chat ID.
3. Put `GROUP_CHAT_ID=<id>` in `backend/.env`.
4. Restart backend **and** bot.
5. Place a test order; tap **Accepted** in the group and watch the group message, the customer tracker and the dashboard sync.

## Verification — exact results (10 Nov 2026)
- **Full backend suite: 21 passed** (`python -m pytest tests/ -q`) — the original 7 plus **14 new** in `backend/tests/test_group_orders.py` covering: forward/backward/noop/invalid transitions, cancel rules + terminal states, keyboard markers (✅/🔵/plain) per status + `callback_data` format, message text (code, items, add-ons, total, table, phone, dict + ORM inputs, "Last updated by"), notify skip when `GROUP_CHAT_ID` empty (no HTTP call made), notify success returning `message_id` with correct chat_id + keyboard payload, Telegram failure swallowed, **order creation still returns 200 while Telegram is down**, and the bot's shared-DB status-change helper (accept → backward rejected → noop → cancel → terminal, verified back through the API).
- **Live boot test** (uvicorn, `GROUP_CHAT_ID` unset, fresh SQLite DB): `GET /health` → ok; `POST /api/orders` → 200, order `BBB805E69A`, total ₹208.95; log showed the notification cleanly skipped (`BOT_TOKEN not set — skipping group notification`). Nothing broke.

## Honest limitations
- **Not live-tested against a real Telegram group** — that needs Sagar's real bot token + a real staff group. Everything up to the Telegram API boundary is unit-tested with mocked httpx, and the callback handler is tested at the shared-DB layer; the one untested hop is Telegram delivering a real tap to the running bot.
- A group message can only be edited while the same bot sent it — guaranteed here because both the API notifier and the bot use the same `BOT_TOKEN`.
- Anyone in the staff group can tap the buttons (by design — it is a staff-only group). Keep the group private.
- Customer DMs only reach customers who have started the bot at least once (Telegram rule) and whose Telegram ID is stored with the order; DMs are best-effort and never block a status change.
