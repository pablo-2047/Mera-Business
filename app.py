"""
Mera Business — AI Business Assistant (Demo Mode)
FastAPI + Chat UI + Gemini AI — no WhatsApp/Facebook dependency
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os, asyncio, logging, uuid
from datetime import datetime
from typing import Optional, Dict, Any
from collections import defaultdict

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Mera Business — AI Business Agent")

BUSINESS_OWNER_PHONE   = os.getenv("BUSINESS_OWNER_PHONE", "")
AUTHORIZED_TEST_PHONES = os.getenv("AUTHORIZED_TEST_PHONES", "").split(",")

message_buffer: Dict[str, Dict[str, Any]] = defaultdict(dict)
buffer_timers:  Dict[str, asyncio.Task]   = {}

MEDIA_DIR = "chat_media"
os.makedirs(MEDIA_DIR, exist_ok=True)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    from database import init_database, get_owner_onboarding_status, create_business_owner
    init_database()
    logger.info("Database ready")

    # Always ensure demo owner exists
    demo_phone = "+919999999999"
    try:
        status = get_owner_onboarding_status(demo_phone)
        if not status['exists'] or not status['onboarding_complete']:
            create_business_owner(phone=demo_phone, name="Demo Owner", business_name="Mera Business Demo")
            logger.info("Demo owner created")
    except Exception as e:
        logger.warning(f"Demo owner seed skipped: {e}")

    asyncio.create_task(udhaar_reminder_scheduler())

# ── Udhaar Reminder Scheduler (daily 10 AM) ───────────────────────────────────
async def udhaar_reminder_scheduler():
    import datetime as dt
    while True:
        now = dt.datetime.now()
        next_run = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run = next_run + dt.timedelta(days=1)
        wait_sec = (next_run - now).total_seconds()
        logger.info(f"Udhaar scheduler: next run in {wait_sec/3600:.1f} hours")
        await asyncio.sleep(wait_sec)
        try:
            await send_udhaar_reminders()
        except Exception as e:
            logger.error(f"Udhaar scheduler error: {e}", exc_info=True)


async def send_udhaar_reminders():
    from database import get_overdue_customers
    owner_ids = [p.strip() for p in [BUSINESS_OWNER_PHONE] + AUTHORIZED_TEST_PHONES if p.strip()]
    owner_ids = owner_ids or ["+919999999999"]
    for owner_id in owner_ids:
        try:
            overdue = get_overdue_customers(days=14, owner_id=owner_id)
            if not overdue:
                continue
            msg = "⏰ *Udhaar Reminder*\n\nIn customers ka payment pending hai:\n\n"
            for c in overdue[:5]:
                days = c.get('days_overdue', 0) or 0
                msg += f"👤 {c['name']} — ₹{c['outstanding_balance']:,.0f} ({days} din से)\n"
            if len(overdue) > 5:
                msg += f"\n...aur {len(overdue)-5} aur customers\n"
            msg += "\nReminder bhejne ke liye naam likho: \"Ramesh ko reminder bhejo\""
            await send_message_to_chat(owner_id, msg)
        except Exception as e:
            logger.error(f"Reminder error for {owner_id}: {e}")


# ── Auth ──────────────────────────────────────────────────────────────────────
def is_authorized(phone: str) -> bool:
    authorized = [BUSINESS_OWNER_PHONE] + [p.strip() for p in AUTHORIZED_TEST_PHONES if p.strip()]
    authorized = [p for p in authorized if p]
    if not authorized:
        return True  # dev/demo mode: allow all
    return phone in authorized


# ── Core message delivery: writes to chat UI history ─────────────────────────
async def send_message_to_chat(to: str, text: str):
    """Write AI response into the in-memory chat history (picked up by /api/chat/messages poll)."""
    try:
        import chat_ui as _cu
        if to not in _cu.CHAT_HISTORY:
            _cu.CHAT_HISTORY[to] = []
        _cu.CHAT_HISTORY[to].append({
            "id": str(uuid.uuid4()),
            "type": "received",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"[CHAT] → {to[:15]}: {text[:60]}")
    except Exception as e:
        logger.error(f"Chat write failed: {e}")


# Keep old name as alias so intent_router / other modules can still call it
send_whatsapp_message = send_message_to_chat


# ── Onboarding ────────────────────────────────────────────────────────────────
ONBOARDING_STATE = {}

async def handle_onboarding(uid: str, text: str):
    from database import create_business_owner
    if uid not in ONBOARDING_STATE:
        ONBOARDING_STATE[uid] = {'step': 'name'}
        await send_message_to_chat(uid,
            "🙏 *Welcome to Mera Business!*\n\n"
            "Please tell me your name / कृपया अपना नाम बताएं:")
        return
    state = ONBOARDING_STATE[uid]
    if state['step'] == 'name':
        state['name'] = text.strip()
        state['step'] = 'business_name'
        await send_message_to_chat(uid,
            f"Nice to meet you, *{state['name']}*! 😊\n\n"
            f"Now tell me your shop/business name / अपनी दुकान का नाम बताएं:")
    elif state['step'] == 'business_name':
        try:
            create_business_owner(phone=uid, name=state['name'], business_name=text.strip())
            ONBOARDING_STATE.pop(uid, None)
            await send_message_to_chat(uid,
                f"✅ *Registration complete!*\n\n"
                f"👤 {state['name']} | 🏪 {text.strip()}\n\n"
                f"Try: \"Ramesh ko phone becha 30000\" or \"Aaj ka hisaab batao\"")
        except Exception as e:
            logger.error(f"Onboarding error: {e}")
            ONBOARDING_STATE.pop(uid, None)
            await send_message_to_chat(uid, "Registration failed. Please try again.")


# ── Process a message through Gemini AI ──────────────────────────────────────
async def process_message(uid: str):
    if uid not in message_buffer:
        return

    if not is_authorized(uid):
        await send_message_to_chat(uid, "Sorry, this is a private assistant.")
        message_buffer.pop(uid, None)
        return

    buf = message_buffer[uid]

    from database import get_owner_onboarding_status
    status = get_owner_onboarding_status(uid)
    if not status['exists'] or not status['onboarding_complete']:
        await handle_onboarding(uid, buf.get("text", ""))
        message_buffer.pop(uid, None)
        return

    try:
        media_path = None
        if buf.get("media_id"):
            # Check if chat UI already provided the path
            if buf.get("media_path") and os.path.exists(buf["media_path"]):
                media_path = buf["media_path"]
            else:
                # Fallback: construct path from media_id
                ext_map = {"audio/ogg":"ogg","audio/mpeg":"mp3","audio/amr":"amr","audio/webm":"webm",
                           "image/jpeg":"jpg","image/png":"png","image/webp":"webp"}
                mime = buf.get("mime_type", "")
                ext = ext_map.get(mime, buf.get("media_type", "bin"))
                candidate = os.path.join(MEDIA_DIR, f"{buf['media_id']}.{ext}")
                if os.path.exists(candidate):
                    media_path = candidate

        from intent_router import route_intent_and_execute
        # Pass conversation history so Gemini has context
        import chat_ui as _cu
        history = _cu.CHAT_HISTORY.get(uid, [])[:-1]  # all msgs except the one just sent
        response = await route_intent_and_execute(
            buf.get("text", ""),
            media_path,
            buf.get("media_type"),
            owner_id=uid,
            conversation_history=history
        )
        await send_message_to_chat(uid, response)
    except Exception as e:
        logger.error(f"Process error: {e}", exc_info=True)
        await send_message_to_chat(uid, "क्षमा करें, कुछ गड़बड़ हो गई। दोबारा कोशिश करें।")
    finally:
        message_buffer.pop(uid, None)
        buffer_timers.pop(uid, None)


async def send_invoice_pdf_to_customer(customer_phone: str, pdf_path: str,
                                        invoice_number: str, owner_id: str):
    """Demo mode: just log it."""
    logger.info(f"[DEMO] Invoice {invoice_number} ready at {pdf_path}")


# ── Health & Routes ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Mera Business AI Agent"}


try:
    import chat_ui
    chat_ui.register_routes(app)
    logger.info("Chat UI routes registered")
except Exception as e:
    logger.error(f"Chat UI import error: {e}", exc_info=True)

try:
    import dashboard
    dashboard.register_routes(app)
    logger.info("Dashboard routes registered")
except Exception as e:
    logger.error(f"Dashboard import error: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    import logging as _logging
    # Silence the noisy poll requests from chat UI in the console
    _logging.getLogger("uvicorn.access").setLevel(_logging.WARNING)
    logger.info("Starting Mera Business server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
