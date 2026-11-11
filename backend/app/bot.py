"""Telegram bot — run: python -m app.bot  (needs BOT_TOKEN, WEBAPP_URL)

Note: this process reads BOT_TOKEN / WEBAPP_URL through app.config
(pydantic-settings), so backend/.env is loaded — the same file the API
process uses. A value set in the terminal session still wins over .env.
The staff-group order buttons work through callback queries, which arrive
with the group message attached, so the bot does not need GROUP_CHAT_ID;
only the API process needs it (in backend/.env) to post the original
group message.
Status changes made here are written to the SAME database the API uses
(shared app.database / app.models), so the Mini App tracker and the admin
dashboard see them immediately.
"""
import asyncio, logging
from .config import settings
logging.basicConfig(level=logging.INFO)
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
except ImportError:
    Update=None
BOT_TOKEN=settings.BOT_TOKEN
WEBAPP_URL=settings.WEBAPP_URL
CAFE="Brew & Bite Cafe"
def kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Order Food 🍔", web_app=WebAppInfo(url=WEBAPP_URL))],[InlineKeyboardButton("Explore Our Menu 📖", web_app=WebAppInfo(url=WEBAPP_URL))]])
async def start(update, ctx):
    await update.message.reply_text(f"Welcome to {CAFE}! ☕🍔\n\nGood vibes, great bites — burgers, pizza, coffee, shakes & more, made fresh for you.\n\nTap below to explore our menu and order in seconds 👇", reply_markup=kb())
async def menu(update, ctx):
    await update.message.reply_text("Explore Our Menu 🍽️ — tap to open the cafe:", reply_markup=kb())
async def orders(update, ctx):
    # Lightweight: instruct + open app (full list needs API auth via Mini App session)
    await update.message.reply_text("Your recent orders are in the Mini App → My Orders tab. Tap below to view & track live 👇", reply_markup=kb())
async def track(update, ctx):
    await update.message.reply_text("Track your latest order live in the Mini App → My Orders. Status: Placed → Accepted → Preparing → Ready → Completed", reply_markup=kb())
async def help_cmd(update, ctx):
    await update.message.reply_text("Help 🆘\n/start — welcome\n/menu — open menu\n/orders — your orders\n/track — track order\n/chatid — (staff) get this group's chat ID for order notifications\n\nNeed help? Call the cafe or ask at the counter.")
async def chatid(update, ctx):
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup"):
        await update.message.reply_text(f"🆔 This group's chat ID is:\n{chat.id}\n\nSetup: copy it into backend/.env as\nGROUP_CHAT_ID={chat.id}\nthen restart the backend. New order notifications with status buttons will arrive in this group.")
    else:
        await update.message.reply_text("To get the staff-group ID:\n1. Add this bot to your cafe staff group\n2. Send /chatid inside that group\nThe bot will reply with the group's chat ID — copy it into backend/.env as GROUP_CHAT_ID.")
async def send_order_confirmation(bot, chat_id, order):
    try:
        await bot.send_message(chat_id=chat_id, text=f"✅ Order confirmed! {order.get('order_code','')}\nTotal: ₹{order.get('total','')} • ETA ~{order.get('eta_mins',25)} mins\nTrack it in the Mini App → My Orders.")
    except Exception as e:
        logging.warning(f"confirmation failed: {e}")

# --- Staff-group order status buttons -------------------------------------
def _apply_status_change(order_code, target, actor):
    """Sync DB work for a button tap. Returns a dict describing the outcome;
    message text/keyboard are built here (inside the DB session) so the
    async handler never touches detached ORM objects."""
    from . import database as dbmod
    from .models import Order
    from .group_orders import build_keyboard, build_message_text, validate_transition, STEP_LABELS
    db = dbmod.SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if not order:
            return {"result": "not_found"}
        allowed, reason = validate_transition(order.status, target)
        if not allowed:
            return {"result": reason, "status": order.status}
        order.status = target
        db.commit()
        return {
            "result": "ok",
            "status": target,
            "label": STEP_LABELS.get(target, target),
            "text": build_message_text(order, updated_by=actor),
            "keyboard": build_keyboard(order.order_code, order.status),
            "telegram_id": order.telegram_id,
            "order_code": order.order_code,
        }
    finally:
        db.close()

def _markup(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(b["text"], callback_data=b["callback_data"]) for b in row] for row in rows])

_DM_LINES = {
    "accepted": "Good news — the cafe accepted your order 👍",
    "preparing": "Your food is being prepared 👨‍🍳",
    "ready": "Your order is ready for pickup 🔔",
    "completed": "Order completed. Enjoy your meal! ✅",
    "cancelled": "Your order was cancelled. Please contact the cafe if this is unexpected.",
}
_ANSWERS = {
    "noop": "ℹ️ Order is already at this step.",
    "backward": "⚠️ Can't go back — the order already passed this step.",
    "terminal": "🔒 This order is already finished.",
    "invalid": "⚠️ Invalid status.",
    "not_found": "❌ Order not found.",
}
async def order_status_callback(update, ctx):
    from .group_orders import parse_callback, STEP_EMOJI
    q = update.callback_query
    code, target = parse_callback(q.data if q else None)
    if not code:
        await q.answer("⚠️ Invalid button."); return
    actor = "Staff"
    if q.from_user:
        actor = q.from_user.full_name or q.from_user.username or "Staff"
    try:
        res = await asyncio.to_thread(_apply_status_change, code, target, actor)
    except Exception as e:
        logging.warning(f"status callback failed: {e}")
        await q.answer("⚠️ Something went wrong — try the admin dashboard."); return
    if res["result"] != "ok":
        await q.answer(_ANSWERS.get(res["result"], "ℹ️ No change.")); return
    await q.answer(f"✅ Status updated: {res['label']}")
    # Edit the group message to the new state (best-effort).
    try:
        await q.edit_message_text(text=res["text"], reply_markup=_markup(res["keyboard"]))
    except Exception as e:
        if "message is not modified" not in str(e):
            logging.warning(f"group message edit failed: {e}")
    # DM the customer their status update (best-effort; never blocks).
    tid = res.get("telegram_id")
    if tid:
        try:
            emoji = STEP_EMOJI.get(res["status"], "🔔")
            line = _DM_LINES.get(res["status"], "")
            await ctx.bot.send_message(chat_id=int(tid) if str(tid).lstrip("-").isdigit() else tid,
                text=f"🔔 Order update — {res['order_code']}\nStatus: {emoji} {res['label']}\n{line}\nTrack live in the Mini App → My Orders.")
        except Exception as e:
            logging.warning(f"customer DM failed: {e}")

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN not set — bot cannot start. Put it in backend/.env (get it from @BotFather) and run the bot from the backend folder."); return
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("menu", menu)); app.add_handler(CommandHandler("orders", orders)); app.add_handler(CommandHandler("track", track)); app.add_handler(CommandHandler("help", help_cmd)); app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CallbackQueryHandler(order_status_callback, pattern=r"^ord:"))
    print(f"Bot running, WebApp: {WEBAPP_URL}"); app.run_polling()
if __name__=="__main__": main()
