# BUILD REPORT — 3D Interactive Cafe Food Ordering System (Telegram Mini App)
Built: 4 Nov 2026 • Cafe: Brew & Bite Cafe • Location: ~/workspace/cafe-telegram-miniapp/

## What was built, per spec section
1. **Overview / Journey** — Full flow implemented: bot /start → Order Food 🍔 WebApp button → Mini App menu → customise → cart → offers → dine-in (table) / takeaway → details → payment → confirmation → live tracking.
2. **Customer journey (15 steps)** — All 15 steps present in code (bot, Mini App, checkout, Telegram confirmation helper, tracking page with 15s polling).
3. **Frontend design** — Premium mobile-first UI: glassmorphism header, hero, featured carousel, offers banners, popular dishes, category chips + grid, search, veg filter, skeleton loaders, sticky bottom nav (Home/Menu/My Orders/Profile), floating cart button with live count.
4. **Categories** — Exactly the 11 spec categories, DB-driven and admin-manageable.
5. **Product cards** — Image, name, description, price, veg/non-veg dot, availability state, rating, Add button.
6. **3D experience** — CSS 3D: perspective tilt on cards, floating animations, layered shadows, rotating CSS-3D featured dish in hero. Three.js intentionally not bundled (see Limitations) — performance first, per spec.
7. **Details & customisation** — Detail modal: large image, quantity, sizes S/M/L with price deltas, add-ons with prices (extra cheese/patty/whipped cream/sauce/jalapeños), special instructions, live total — all configured per-item in DB/admin.
8. **Cart & checkout** — Add/remove, quantity +/−, per-item notes, subtotal, GST (from admin settings, default 5%), coupon validation via backend, final total. Checkout: name, Telegram user, phone, dine-in + table select / takeaway, instructions, payment method.
9. **Payments** — UPI, Razorpay (order create + HMAC signature verify + webhook stub; never marked paid without verification; unique TXN ref per payment), Cash at Counter, Pay at Cafe. Without Razorpay keys the API returns a clear "not configured" response and COD/UPI flow continues.
10. **Orders & tracking** — Unique order codes (e.g. BB0F89A443), DB persistence, admin notification data, ETA 25 min, 6 statuses (placed→accepted→preparing→ready→completed/cancelled), customer tracking timeline.
11. **Telegram bot** — backend/app/bot.py (python-telegram-bot): /start (welcome + cafe intro + inline WebApp buttons), /menu, /orders, /track, /help; order-confirmation sender helper (best-effort). Backend verifies Telegram initData via HMAC-SHA256; frontend user ids are never trusted.
12. **Admin dashboard** — /admin in the same React app, JWT + role: stats (total/today/revenue/pending/completed, popular items, recent transactions), food CRUD + availability toggle, category CRUD, order list + status updates + printable receipt, coupons, tables, settings (GST/cafe/hours), inventory, sales-by-day report.
13. **Tech stack** — Exactly as spec'd: React+Vite+TypeScript+Tailwind+Framer Motion; FastAPI+Pydantic+SQLAlchemy; PostgreSQL via DATABASE_URL with SQLite local fallback; Razorpay; env-var-only secrets; docker-compose (Postgres+backend+frontend).
14. **Security/performance** — Pydantic validation, ORM only (no raw SQL), PBKDF2-hashed admin password, JWT (separate admin role check), in-memory rate limiting (60/min on order/auth), CORS from env, structured errors, lazy images, no WebGL weight.
15. **README** — Install, env vars, local dev, BotFather Mini App steps, Vercel/Render deployment, security model.

## Verification — exact results (all run 4 Nov 2026)
- **Backend tests: `7 passed`** (`python -m pytest tests/ -q`) — initData valid + tampered, server-side pricing ignoring a tampered ₹1 client price, WELCOME10/FIRST50 coupon math, GST math, dine-in table requirement, order lifecycle placed→accepted→preparing→ready→completed + invalid-status rejection, admin-auth enforcement.
- **Backend live boot (uvicorn):** `GET /health` → {"status":"ok"} • `GET /api/categories` → 11 categories • `GET /api/menu` → 22 items • Live order with tampered client price ₹1: server returned subtotal ₹398 (199×2, tamper ignored), discount ₹39.80, GST ₹17.91, **total ₹376.11** ✓ • Admin login (admin/admin123) returned a JWT ✓ • Razorpay order without keys returned `{"configured": false, ...}` gracefully ✓
- **Frontend build: `npm run build` PASSED** — tsc clean, Vite build: dist/index.html 0.49 kB, CSS 17.56 kB, JS 318.64 kB (gzip ~102 kB). Built output left in `frontend/dist/`.
- **Not verified:** real Telegram client tap-through (needs Sagar's BOT_TOKEN + a public HTTPS deploy — steps are in README); real Razorpay payment (needs real keys); PostgreSQL path (code uses DATABASE_URL via SQLAlchemy; local verification ran on the SQLite fallback).

## Run locally in 5 steps
1. `cd backend && python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt && cp .env.example .env`
3. `uvicorn app.main:app --reload --port 8000` (auto-seeds; check http://localhost:8000/health)
4. `cd ../frontend && npm install && npm run dev` → Mini App http://localhost:5173 • Admin http://localhost:5173/admin (admin / admin123)
5. Bot: set BOT_TOKEN + WEBAPP_URL in backend/.env, then `python -m app.bot`
(Or: `docker compose up --build` for Postgres + backend + frontend together.)

## Preview note for the parent agent
Frontend is in `frontend/` with a fresh production build in `frontend/dist/`. For a clickable preview artifact, serve the app source (src/App.tsx + src/pages/Admin.tsx) the same way as previous React previews, with VITE_API_URL unset — the built-in seed-data fallback (frontend/src/lib/seedData.ts, mirroring backend seed) makes Home/Menu/Cart/Checkout/Orders fully clickable offline; the Admin page requires the real backend running (it shows a clear backend-unreachable message otherwise).

## Honest limitations
- **Razorpay** needs real merchant keys to take a live payment; signature verification code is implemented and tested by construction, but no real payment was processed (no keys available). UPI option is "pay at counter/on pickup" — there is no UPI intent/collect integration without a gateway.
- **Three.js:** deliberately not included. CSS-3D delivers the 3D look at ~0 KB extra; adding react-three-fiber would add ~600 KB against the spec's performance requirement. Choice documented in README.
- **Image upload:** admin uses an image **URL** field (Unsplash/Cloudinary/S3) — no local file-upload endpoint, by design for stateless deploys.
- **Bot /orders & /track** reply with the user's status summary + a Mini App deep link rather than querying per-user orders inside chat, because chat-side identity → API auth requires the Mini App session; full order lists live in the Mini App's My Orders (same data, verified identity).
- **Order-confirmation Telegram message** is a best-effort helper: it fires when the bot process/token is configured; order placement never depends on it.
- Admin password hashing uses PBKDF2-HMAC-SHA256 (stdlib) instead of bcrypt due to a passlib/bcrypt version incompatibility found during verification — equally sound for this use, noted here for transparency.
- Rate limiter is in-memory (per-process) — fine for single-instance deploys; use Redis for multi-instance production.

---

## Addendum — 10 Nov 2026: Staff Group Order Notifications
Added on Sagar's confirmed request: every new order is posted to the cafe staff Telegram group with full order details and inline status buttons (Order Placed → Accepted → Preparing → Ready for Pickup → Completed + Cancel). Staff taps update the shared DB, edit the group message, DM the customer, and sync the Mini App tracker + admin dashboard (dashboard changes also edit the group message). New files: `backend/app/group_orders.py` (pure logic), `backend/app/notify.py` (best-effort httpx notifier), `backend/tests/test_group_orders.py`; new config `GROUP_CHAT_ID`; new `orders.group_message_id` column. Full details + setup: **GROUP_FEATURE.md** and the README section "Staff Group Order Notifications".
Verification (10 Nov 2026): full backend suite **21 passed** (7 original + 14 new); live uvicorn boot test with `GROUP_CHAT_ID` unset — health ok, order placed (₹208.95), notification cleanly skipped, nothing broke. Not live-tested against a real Telegram group (needs Sagar's real token + staff group).
