"""
Mera Business — WhatsApp-Like Chat Interface for Demo/Testing
Identical UI to WhatsApp with text, voice, image support
"""

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
import os
import uuid
from datetime import datetime
import asyncio
import logging

CHAT_HISTORY = {}  # phone -> [messages]

logger = logging.getLogger(__name__)

# Use an APIRouter to avoid circular import with app.py
router = APIRouter()

def register_routes(app):
    app.include_router(router)

# Create media directory for chat uploads
CHAT_MEDIA_DIR = "chat_media"
os.makedirs(CHAT_MEDIA_DIR, exist_ok=True)


@router.get("/chat", response_class=HTMLResponse)
async def chat_interface():
    """WhatsApp-like chat interface for demo"""
    return HTMLResponse(CHAT_UI_HTML)


@router.post("/api/chat/send")
async def send_chat_message(request: Request):
    """Send text message from chat UI"""
    try:
        data = await request.json()
        phone = data.get('phone', '+919999999999')  # Demo user
        message = data.get('message', '').strip()
        
        if not message:
            return JSONResponse({"success": False, "error": "Empty message"})
        
        # Add sent message to chat history
        msg_id = str(uuid.uuid4())
        if phone not in CHAT_HISTORY:
            CHAT_HISTORY[phone] = []
        CHAT_HISTORY[phone].append({
            "id": msg_id,
            "type": "sent",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        })
        
        # Directly process the message (bypass buffer/timer for chat UI)
        from app import message_buffer, process_message
        message_buffer[phone] = {
            "text": message,
            "media_id": None,
            "media_type": None,
            "mime_type": None
        }
        await process_message(phone)
        
        return JSONResponse({"success": True, "message_id": msg_id})
        
    except Exception as e:
        logger.error(f"Chat send error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/api/chat/upload-voice")
async def upload_voice_message(
    phone: str = Form('+919999999999'),
    audio: UploadFile = File(...)
):
    """Upload voice message from chat UI"""
    try:
        # Save audio file
        file_id = str(uuid.uuid4())
        # Detect format: webm from MediaRecorder, or ogg from file upload
        ext = 'webm' if audio.content_type == 'audio/webm' else 'ogg'
        file_path = os.path.join(CHAT_MEDIA_DIR, f"{file_id}.{ext}")
        
        with open(file_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Add to chat history
        if phone not in CHAT_HISTORY:
            CHAT_HISTORY[phone] = []
        
        CHAT_HISTORY[phone].append({
            "id": file_id,
            "type": "sent",
            "content": "🎤 Voice message",
            "media_path": file_path,
            "media_type": "audio",
            "timestamp": datetime.now().isoformat(),
            "status": "sending"
        })
        
        # Process through AI
        from app import message_buffer
        message_buffer[phone] = {
            "text": None,
            "media_id": file_id,
            "media_type": "audio",
            "mime_type": "audio/ogg",
            "media_path": file_path  # Direct path for local processing
        }
        
        # Process
        await asyncio.sleep(0.5)
        from app import process_message as pm
        await pm(phone)
        
        # Update status
        CHAT_HISTORY[phone][-1]["status"] = "sent"
        
        return JSONResponse({"success": True, "file_id": file_id})
        
    except Exception as e:
        logger.error(f"Voice upload error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/api/chat/upload-image")
async def upload_image_message(
    phone: str = Form('+919999999999'),
    image: UploadFile = File(...),
    caption: str = Form(None)
):
    """Upload image message from chat UI"""
    try:
        # Save image file
        file_id = str(uuid.uuid4())
        ext = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        file_path = os.path.join(CHAT_MEDIA_DIR, f"{file_id}.{ext}")
        
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # Add to chat history
        if phone not in CHAT_HISTORY:
            CHAT_HISTORY[phone] = []
        
        CHAT_HISTORY[phone].append({
            "id": file_id,
            "type": "sent",
            "content": caption or "📷 Image",
            "media_path": file_path,
            "media_type": "image",
            "timestamp": datetime.now().isoformat(),
            "status": "sending"
        })
        
        # Process through AI
        from app import message_buffer
        message_buffer[phone] = {
            "text": caption,
            "media_id": file_id,
            "media_type": "image",
            "mime_type": f"image/{ext}",
            "media_path": file_path
        }
        
        await asyncio.sleep(0.5)
        from app import process_message as pm
        await pm(phone)
        
        # Update status
        CHAT_HISTORY[phone][-1]["status"] = "sent"
        
        return JSONResponse({"success": True, "file_id": file_id})
        
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)})


@router.get("/api/chat/messages")
async def get_chat_messages(phone: str = '+919999999999'):
    """Get chat message history"""
    messages = CHAT_HISTORY.get(phone, [])
    return JSONResponse({"messages": messages})


@router.post("/api/chat/clear")
async def clear_chat_history(request: Request):
    """Clear chat history for a phone (resets conversation context)"""
    data = await request.json()
    phone = data.get('phone', '+919999999999')
    CHAT_HISTORY.pop(phone, None)
    return JSONResponse({"success": True})


# NOTE: In the string below, \\n is used instead of \n to prevent 
# Python from breaking the JavaScript regex logic.
CHAT_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mera Business - Chat Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            background: #0a1014;
            height: 100vh;
            overflow: hidden;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 1200px;
            margin: 0 auto;
            background: #111b21;
        }
        
        /* Header */
        .chat-header {
            background: #202c33;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid #2a3942;
        }
        
        .avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00a884, #00d4aa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        
        .chat-info {
            flex: 1;
        }
        
        .chat-name {
            color: #e9edef;
            font-size: 18px;
            font-weight: 500;
        }
        
        .chat-status {
            color: #8696a0;
            font-size: 13px;
            margin-top: 2px;
        }
        
        /* Messages Area */
        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23111b21"/></svg>');
            background-repeat: repeat;
        }
        
        .message {
            display: flex;
            margin-bottom: 12px;
            animation: slideIn 0.2s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.sent {
            justify-content: flex-end;
        }
        
        .message-bubble {
            max-width: 65%;
            padding: 8px 12px;
            border-radius: 8px;
            position: relative;
            word-wrap: break-word;
        }
        
        .message.sent .message-bubble {
            background: #005c4b;
            color: #e9edef;
            border-radius: 8px 0 8px 8px;
        }
        
        .message.received .message-bubble {
            background: #202c33;
            color: #e9edef;
            border-radius: 0 8px 8px 8px;
        }
        
        .message-text {
            line-height: 1.5;
            white-space: pre-wrap;
        }
        
        .message-time {
            font-size: 11px;
            color: #8696a0;
            text-align: right;
            margin-top: 4px;
        }
        
        .message.sent .message-time {
            color: #99e1d3;
        }
        
        /* Input Area */
        .input-area {
            background: #202c33;
            padding: 10px 15px;
            display: flex;
            gap: 10px;
            align-items: center;
            border-top: 1px solid #2a3942;
        }
        
        .input-actions {
            display: flex;
            gap: 8px;
        }
        
        .action-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: #8696a0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        .action-btn:hover {
            background: #2a3942;
            color: #aebac1;
        }
        
        .message-input {
            flex: 1;
            background: #2a3942;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            color: #e9edef;
            font-size: 15px;
            outline: none;
        }
        
        .message-input::placeholder {
            color: #667781;
        }
        
        .send-btn {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: #00a884;
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        .send-btn:hover {
            background: #00d4aa;
        }
        
        .send-btn:disabled {
            background: #2a3942;
            color: #667781;
            cursor: not-allowed;
        }
        
        /* Loading indicator */
        .typing-indicator {
            display: none;
            padding: 8px 12px;
            background: #202c33;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        
        .typing-indicator.active {
            display: flex;
            gap: 4px;
        }
        
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #8696a0;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .dot:nth-child(2) { animation-delay: -0.32s; }
        .dot:nth-child(3) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        /* Hidden file inputs */
        #voiceInput, #imageInput {
            display: none;
        }
        
        /* Welcome banner */
        .welcome-banner {
            text-align: center;
            padding: 40px 20px;
            color: #8696a0;
        }
        
        .welcome-banner h2 {
            color: #e9edef;
            margin-bottom: 10px;
        }
        
        .welcome-banner p {
            margin: 5px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="avatar">🏪</div>
            <div class="chat-info">
                <div class="chat-name">Mera Business AI</div>
                <div class="chat-status">Online • Demo Mode</div>
            </div>
            <button onclick="clearChat()" style="background:#2a3942;border:none;color:#8696a0;padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px;">🗑 Clear</button>
        </div>
        
        <div class="messages-area" id="messagesArea">
            <div class="welcome-banner">
                <h2>Welcome to Mera Business!</h2>
                <p>Your AI-powered business assistant</p>
                <p>Try: "Ramesh ko phone becha 30000"</p>
                <p>Or: "Aaj ka hisaab batao"</p>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
        
        <div class="input-area">
            <div class="input-actions">
                <button class="action-btn" id="voiceBtn" onclick="toggleVoiceRecording()" title="Voice message">
                    🎤
                </button>
                <button class="action-btn" onclick="triggerImage()" title="Send image">
                    📷
                </button>
            </div>
            
            <span class="recording-timer" id="recordingTimer">0:00</span>
            
            <input type="text" 
                   class="message-input" 
                   id="messageInput" 
                   placeholder="Type a message" 
                   autocomplete="off">
            
            <button class="send-btn" id="sendBtn" onclick="sendMessage()">
                ➤
            </button>
            
            <input type="file" id="imageInput" accept="image/*" onchange="sendImage()">
        </div>
    </div>
    
    <script>
        const phone = '+919999999999';
        let isProcessing = false;
        let lastMsgCount = 0;
        
        // Voice recording state
        let mediaRecorder = null;
        let audioChunks = [];
        let recordingStartTime = null;
        let recordingTimerInterval = null;

        // Initial load + poll every 1.5s
        loadMessages();
        setInterval(loadMessages, 1500);

        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });

        function triggerImage() { document.getElementById('imageInput').click(); }

        async function clearChat() {
            if (!confirm('Clear all messages?')) return;
            await fetch('/api/chat/clear', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone})
            });
            lastMsgCount = 0;
            document.getElementById('messagesArea').innerHTML = `
                <div class="welcome-banner">
                    <h2>Welcome to Mera Business!</h2>
                    <p>Your AI-powered business assistant</p>
                    <p>Try: "Ramesh ko phone becha 30000"</p>
                    <p>Or: "Aaj ka hisaab batao"</p>
                </div>`;
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message || isProcessing) return;

            isProcessing = true;
            document.getElementById('sendBtn').disabled = true;
            input.value = '';
            showTyping();

            try {
                const res = await fetch('/api/chat/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone, message})
                });
                const data = await res.json();
                if (!data.success) console.error('Send failed:', data.error);
                await loadMessages();
            } catch (err) {
                console.error('Send error:', err);
            } finally {
                isProcessing = false;
                document.getElementById('sendBtn').disabled = false;
                hideTyping();
                input.focus();
            }
        }
        
        // Voice Recording with MediaRecorder API
        async function toggleVoiceRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                // Stop recording
                stopVoiceRecording();
            } else {
                // Start recording
                startVoiceRecording();
            }
        }
        
        async function startVoiceRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioChunks = [];
                
                // Use webm/opus if supported, fallback to default
                const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                    ? { mimeType: 'audio/webm;codecs=opus' }
                    : {};
                
                mediaRecorder = new MediaRecorder(stream, options);
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await sendVoiceBlob(audioBlob);
                    
                    // Stop all tracks to release microphone
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                recordingStartTime = Date.now();
                
                // Update UI
                const voiceBtn = document.getElementById('voiceBtn');
                voiceBtn.classList.add('recording');
                voiceBtn.title = 'Stop recording';
                
                const timer = document.getElementById('recordingTimer');
                timer.classList.add('active');
                
                // Start timer
                recordingTimerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
                    const minutes = Math.floor(elapsed / 60);
                    const seconds = elapsed % 60;
                    timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                }, 100);
                
            } catch (err) {
                console.error('Microphone access error:', err);
                alert('Could not access microphone. Please allow microphone permission.');
            }
        }
        
        function stopVoiceRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                
                // Clear timer
                if (recordingTimerInterval) {
                    clearInterval(recordingTimerInterval);
                    recordingTimerInterval = null;
                }
                
                // Reset UI
                const voiceBtn = document.getElementById('voiceBtn');
                voiceBtn.classList.remove('recording');
                voiceBtn.title = 'Voice message';
                
                const timer = document.getElementById('recordingTimer');
                timer.classList.remove('active');
                timer.textContent = '0:00';
            }
        }
        
        async function sendVoiceBlob(audioBlob) {
            if (isProcessing) return;
            isProcessing = true;
            showTyping();
            
            try {
                const fd = new FormData();
                fd.append('phone', phone);
                fd.append('audio', audioBlob, 'recording.webm');
                
                const res = await fetch('/api/chat/upload-voice', {
                    method: 'POST',
                    body: fd
                });
                
                await loadMessages();
            } catch (e) {
                console.error('Voice upload error:', e);
            } finally {
                isProcessing = false;
                hideTyping();
            }
        }

        async function sendImage() {
            const input = document.getElementById('imageInput');
            const file = input.files[0];
            if (!file || isProcessing) return;
            isProcessing = true; showTyping();
            try {
                const fd = new FormData();
                fd.append('phone', phone); fd.append('image', file); fd.append('caption','');
                const res = await fetch('/api/chat/upload-image', {method:'POST', body:fd});
                await loadMessages();
            } catch(e){ console.error(e); }
            finally { isProcessing=false; hideTyping(); input.value=''; }
        }

        async function loadMessages() {
            try {
                const res = await fetch(`/api/chat/messages?phone=${encodeURIComponent(phone)}`);
                const data = await res.json();
                renderMessages(data.messages || []);
            } catch(e) { console.error('Load error:', e); }
        }

        function renderMessages(messages) {
            const area = document.getElementById('messagesArea');
            const atBottom = area.scrollHeight - area.scrollTop <= area.clientHeight + 50;

            if (messages.length === 0) {
                if (lastMsgCount === 0) area.innerHTML = `
                    <div class="welcome-banner">
                        <h2>Welcome to Mera Business!</h2>
                        <p>Your AI-powered business assistant</p>
                        <p>Try: "Ramesh ko phone becha 30000"</p>
                        <p>Or: "Aaj ka hisaab batao"</p>
                    </div>`;
                return;
            }
            if (messages.length === lastMsgCount) return; // no change, skip re-render
            lastMsgCount = messages.length;

            area.innerHTML = messages.map(msg => `
                <div class="message ${msg.type}">
                    <div class="message-bubble">
                        <div class="message-text">${escapeHtml(msg.content)}</div>
                        <div class="message-time">${formatTime(msg.timestamp)}</div>
                    </div>
                </div>`).join('');

            if (atBottom) area.scrollTop = area.scrollHeight;
        }

        function showTyping() { document.getElementById('typingIndicator').classList.add('active'); }
        function hideTyping() { document.getElementById('typingIndicator').classList.remove('active'); }

        function formatTime(ts) {
            return new Date(ts).toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'});
        }

        function escapeHtml(text) {
            return String(text)
                .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                .replace(/\\n/g,'<br>');
        }
    </script>
</body>
</html>
"""