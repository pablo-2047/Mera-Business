"""
<<<<<<< HEAD
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
=======
Bharat Biz-Agent - WhatsApp Gateway Server
FastAPI webhook for Meta WhatsApp Cloud API integration
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import os
import httpx
import time
import json
from typing import Optional, Dict, Any, List
import asyncio
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bharat Biz-Agent Gateway")

# Configuration from environment variables
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "bharat_biz_agent_2026")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Authorization for hackathon demo (single business owner)
# For production: Replace with multi-tenant owner_id lookup
BUSINESS_OWNER_PHONE = os.getenv("BUSINESS_OWNER_PHONE", "")  # Your phone number
AUTHORIZED_TEST_PHONES = os.getenv("AUTHORIZED_TEST_PHONES", "").split(",")  # Judges' phones

# Message buffer for handling multi-part messages (text + media)
message_buffer: Dict[str, Dict[str, Any]] = defaultdict(dict)
buffer_timers: Dict[str, asyncio.Task] = {}

# Constants
BUFFER_WAIT_TIME = 2  # seconds to wait for merged messages
MEDIA_DOWNLOAD_DIR = "/tmp/whatsapp_media"
os.makedirs(MEDIA_DOWNLOAD_DIR, exist_ok=True)


def is_authorized_user(phone_number: str) -> bool:
    """
    Check if this phone number is authorized to use the system
    
    For Hackathon Demo: Simple whitelist
    For Production: Would check business_owners table with owner_id
    
    Args:
        phone_number: User's WhatsApp phone number
        
    Returns:
        True if authorized, False otherwise
    """
    # For hackathon: Owner + test phones (judges)
    authorized_phones = [BUSINESS_OWNER_PHONE] + [p.strip() for p in AUTHORIZED_TEST_PHONES if p.strip()]
    
    # Remove empty strings
    authorized_phones = [p for p in authorized_phones if p]
    
    # Allow if no restrictions set (for development)
    if not authorized_phones:
        logger.warning("No authorized phones set - allowing all access (dev mode)")
        return True
    
    # Check if user is authorized
    is_auth = phone_number in authorized_phones
    
    if not is_auth:
        logger.warning(f"Unauthorized access attempt from: {phone_number}")
    
    return is_auth


class WhatsAppMessage(BaseModel):
    """Model for incoming WhatsApp messages"""
    message_id: str
    from_number: str
    timestamp: str
    message_type: str
    text_content: Optional[str] = None
    media_id: Optional[str] = None
    media_type: Optional[str] = None
    media_mime_type: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Bharat Biz-Agent Gateway"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    GET webhook verification for Meta WhatsApp Cloud API
    
    Meta will send a GET request with:
    - hub.mode=subscribe
    - hub.verify_token=<your_token>
    - hub.challenge=<random_string>
    
    We must validate the token and return the challenge.
    """
    params = request.query_params
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    logger.info(f"Webhook verification request - Mode: {mode}, Token match: {token == VERIFY_TOKEN}")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    POST webhook for receiving WhatsApp messages
    
    This handles:
    1. Text messages
    2. Voice messages (audio)
    3. Images
    4. Documents
    
    Implements buffering strategy to merge text + media into single AI call
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")
        
        # Parse the incoming webhook payload
        if "entry" not in body:
            return JSONResponse({"status": "no_entry"}, status_code=200)
        
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Extract message data
                messages = value.get("messages", [])
                for message in messages:
                    parsed_message = parse_whatsapp_message(message)
                    if parsed_message:
                        # Add to buffer and schedule processing
                        background_tasks.add_task(
                            buffer_and_process_message,
                            parsed_message
                        )
        
        return JSONResponse({"status": "ok"}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=200)


def parse_whatsapp_message(message: dict) -> Optional[WhatsAppMessage]:
    """
    Parse WhatsApp message payload into structured format
    
    Args:
        message: Raw message dict from WhatsApp webhook
        
    Returns:
        WhatsAppMessage or None if invalid
    """
    try:
        msg_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        msg_type = message.get("type")
        
        parsed = WhatsAppMessage(
            message_id=msg_id,
            from_number=from_number,
            timestamp=timestamp,
            message_type=msg_type
        )
        
        # Extract content based on type
        if msg_type == "text":
            parsed.text_content = message.get("text", {}).get("body")
            
        elif msg_type == "audio":
            audio = message.get("audio", {})
            parsed.media_id = audio.get("id")
            parsed.media_type = "audio"
            parsed.media_mime_type = audio.get("mime_type")
            
        elif msg_type == "image":
            image = message.get("image", {})
            parsed.media_id = image.get("id")
            parsed.media_type = "image"
            parsed.media_mime_type = image.get("mime_type")
            parsed.text_content = image.get("caption")  # Optional caption
            
        elif msg_type == "document":
            doc = message.get("document", {})
            parsed.media_id = doc.get("id")
            parsed.media_type = "document"
            parsed.media_mime_type = doc.get("mime_type")
            parsed.text_content = doc.get("caption")
            
        return parsed
        
    except Exception as e:
        logger.error(f"Error parsing message: {str(e)}", exc_info=True)
        return None


async def buffer_and_process_message(message: WhatsAppMessage):
    """
    Buffer strategy: Wait for text + media to arrive as pair
    
    WhatsApp sends text and media as separate messages.
    We wait 2 seconds to see if both parts arrive, then process together.
    
    Args:
        message: Parsed WhatsApp message
    """
    user_id = message.from_number
    
    # Add to buffer
    if message.text_content:
        message_buffer[user_id]["text"] = message.text_content
        message_buffer[user_id]["text_timestamp"] = time.time()
        
    if message.media_id:
        message_buffer[user_id]["media_id"] = message.media_id
        message_buffer[user_id]["media_type"] = message.media_type
        message_buffer[user_id]["media_mime_type"] = message.media_mime_type
        message_buffer[user_id]["media_timestamp"] = time.time()
    
    # Cancel existing timer if any
    if user_id in buffer_timers:
        buffer_timers[user_id].cancel()
    
    # Set new timer
    async def process_after_wait():
        await asyncio.sleep(BUFFER_WAIT_TIME)
        await process_buffered_message(user_id)
    
    buffer_timers[user_id] = asyncio.create_task(process_after_wait())


async def process_buffered_message(user_id: str):
    """
    Process the complete buffered message (text + optional media)
    
    Args:
        user_id: User's phone number
    """
    if user_id not in message_buffer:
        return
    
    # Check authorization FIRST
    if not is_authorized_user(user_id):
        logger.warning(f"Unauthorized user attempted access: {user_id}")
        await send_whatsapp_message(
            user_id,
            "क्षमा करें, यह एक निजी व्यवसाय सहायक है। पहुँच प्रतिबंधित है।\n\n"
            "Sorry, this is a private business assistant. Access is restricted.\n\n"
            "For demo access, please contact the business owner."
        )
        # Clear buffer
        if user_id in message_buffer:
            del message_buffer[user_id]
        if user_id in buffer_timers:
            del buffer_timers[user_id]
        return
    
    buffer_data = message_buffer[user_id]
    logger.info(f"Processing buffered message for authorized user {user_id}: {buffer_data}")
    
    try:
        # Download media if present
        media_file_path = None
        if "media_id" in buffer_data:
            media_file_path = await download_whatsapp_media(
                buffer_data["media_id"],
                buffer_data["media_type"],
                buffer_data.get("media_mime_type")
            )
        
        # Get text content
        text_content = buffer_data.get("text", "")
        
        # Send to Gemini for intent routing
        response = await route_to_gemini(text_content, media_file_path, buffer_data.get("media_type"))
        
        # Send response back to WhatsApp
        await send_whatsapp_message(user_id, response)
        
    except Exception as e:
        logger.error(f"Error processing buffered message: {str(e)}", exc_info=True)
        await send_whatsapp_message(user_id, "क्षमा करें, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।")
        
    finally:
        # Clear buffer
        if user_id in message_buffer:
            del message_buffer[user_id]
        if user_id in buffer_timers:
            del buffer_timers[user_id]


async def download_whatsapp_media(media_id: str, media_type: str, mime_type: Optional[str] = None) -> str:
    """
    Download media file from WhatsApp Cloud API
    
    Process:
    1. Get media URL using media_id
    2. Download actual file binary
    3. Save to local storage
    
    Args:
        media_id: WhatsApp media ID
        media_type: audio/image/document
        mime_type: MIME type of media
        
    Returns:
        Local file path
    """
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Get media URL
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            media_data = response.json()
            media_url = media_data.get("url")
            
            if not media_url:
                raise Exception("No media URL in response")
            
            # Step 2: Download actual file
            download_response = await client.get(media_url, headers=headers)
            download_response.raise_for_status()
            
            # Step 3: Save to file
            extension = get_file_extension(mime_type, media_type)
            file_path = os.path.join(MEDIA_DOWNLOAD_DIR, f"{media_id}{extension}")
            
            with open(file_path, "wb") as f:
                f.write(download_response.content)
            
            logger.info(f"Downloaded media to {file_path}")
            return file_path
            
    except Exception as e:
        logger.error(f"Error downloading media: {str(e)}", exc_info=True)
        raise


def get_file_extension(mime_type: Optional[str], media_type: str) -> str:
    """Get file extension based on MIME type"""
    if not mime_type:
        return f".{media_type}"
    
    mime_map = {
        "audio/ogg": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/amr": ".amr",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }
    
    return mime_map.get(mime_type, f".{media_type}")


async def route_to_gemini(text: str, media_path: Optional[str], media_type: Optional[str]) -> str:
    """
    Send message to Gemini for intent routing and action execution
    
    This bridges WhatsApp messages to the Gemini intent router which:
    1. Understands Hindi/Hinglish/English
    2. Decides which function to call
    3. Executes database operations
    4. Returns natural language response
    
    Args:
        text: Text content from user
        media_path: Local path to downloaded media (if any)
        media_type: Type of media (audio/image/document)
        
    Returns:
        Response message to send back to user
    """
    from intent_router import route_intent_and_execute
    
    logger.info(f"Routing to Gemini - Text: {text}, Media: {media_path}, Type: {media_type}")
    
    try:
        # Call the intent router with multimodal input
        response = await route_intent_and_execute(text, media_path, media_type)
        return response
    except Exception as e:
        logger.error(f"Error in Gemini routing: {str(e)}", exc_info=True)
        return "क्षमा करें, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।"


async def send_whatsapp_message(to_number: str, message: str):
    """
    Send a text message back to WhatsApp user
    
    Args:
        to_number: Recipient's phone number
        message: Text message to send
    """
    try:
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Sent message to {to_number}: {message[:50]}...")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
>>>>>>> 7e4398ab37a263c75b381f78a874db8edee8182f


if __name__ == "__main__":
    import uvicorn
<<<<<<< HEAD
    import logging as _logging
    # Silence the noisy poll requests from chat UI in the console
    _logging.getLogger("uvicorn.access").setLevel(_logging.WARNING)
    logger.info("Starting Mera Business server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
=======
    uvicorn.run(app, host="0.0.0.0", port=8000)
>>>>>>> 7e4398ab37a263c75b381f78a874db8edee8182f
