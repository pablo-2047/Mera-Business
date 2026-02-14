# 🇮🇳 Mera Business — WhatsApp AI Agent for Indian SMBs

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)
![Gemini](https://img.shields.io/badge/Gemini-2.5--flash-orange?logo=google)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A WhatsApp-first AI business assistant for India's 60M+ small shop owners.**  
No app download. No training. Just WhatsApp — in Hindi, Hinglish, or English.

</div>

---

## 📱 How It Works

```
Shop Owner's WhatsApp  →  Meta Cloud API  →  Your Server  →  Gemini AI  →  SQLite DB  →  Reply
```

The owner simply chats with a WhatsApp number. The entire business logic runs on your server — completely invisible to them.

**Example conversation:**
```
Owner: "Ramesh ko Vivo V29 becha 29999 mein"
Agent: ✅ Invoice created!
       📄 INV20260214001
       👤 Ramesh Kumar
       📱 Vivo V29 × 1
       💰 Subtotal: ₹29,999 | GST: ₹5,400 | Total: ₹35,399
       📦 Stock: 49 units remaining

Owner: "Aaj ka hisaab"
Agent: 📊 Today's Summary (14/02/2026)
       💰 Sales: 3 invoices — ₹1,05,000
       💸 Payments received: ₹75,000
       ⚠️  Outstanding: ₹30,000
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧾 Invoice Creation | Hindi/Hinglish voice or text → auto-generate GST invoice |
| 💰 Payment Tracking | Record UPI/cash payments, auto-update outstanding balance |
| 📦 Inventory Management | Real-time stock updates, low-stock alerts |
| 👥 Customer Ledger | Udhaar tracking, overdue reminders |
| 📊 Daily Summary | One message gets full P&L for the day |
| 📄 PDF Invoices | Professional invoice PDF generation |
| 🎤 Voice Support | Audio messages transcribed and processed |
| 🌐 Multilingual | Hindi, Hinglish, English — auto-detected |
| ⚡ Context Caching | 90% cost reduction via Gemini Context Cache |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 User's WhatsApp                      │
│          (their own number — no app needed)         │
└──────────────────────┬──────────────────────────────┘
                       │  Message
                       ▼
┌─────────────────────────────────────────────────────┐
│              Meta WhatsApp Cloud API                │
│      (delivers message via HTTP POST webhook)       │
└──────────────────────┬──────────────────────────────┘
                       │  Webhook POST
                       ▼
┌─────────────────────────────────────────────────────┐
│           FastAPI Server  (app.py)                  │
│  • Webhook verification                             │
│  • Message buffering (text + media merging)         │
│  • Authorization check                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         Intent Router  (intent_router.py)           │
│  • Gemini 2.5 Flash with function calling           │
│  • Context Caching (system + tools cached 1hr)      │
│  • Fallback to pattern matcher if API fails         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           Database Layer  (database.py)             │
│  • SQLite with WAL mode                             │
│  • Invoices, Payments, Inventory, Customers         │
│  • Udhaar ledger, GST records, Activity log         │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Gemini API Key](https://aistudio.google.com/app/apikey) (free)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/) (free tier: 1000 msgs/month)
- [ngrok](https://ngrok.com) for local development

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/Mera-Business.git
cd Mera-Business

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
WHATSAPP_VERIFY_TOKEN=your_custom_token
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
GEMINI_API_KEY=AIzaSyxxxxxxxxx
BUSINESS_OWNER_PHONE=+919876543210
AUTHORIZED_TEST_PHONES=+919988776655,+919123456789
```

### 3. Initialize Database

```bash
python database.py
```

### 4. Start Server

```bash
uvicorn app:app --reload --port 8000
```

### 5. Expose with ngrok

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL and set it as your WhatsApp webhook:
```
https://xxxx.ngrok.io/webhook
```

---

## 💬 Supported Commands

| Input (Hindi/Hinglish) | Action |
|------------------------|--------|
| `Ramesh ko phone becha 30000` | Create invoice |
| `Suresh ko Samsung udhaar pe diya` | Create credit sale |
| `Ramesh se 5000 payment aaya UPI se` | Record payment |
| `Aaj ka hisaab batao` | Daily summary |
| `iPhone ka stock kitna hai` | Check stock |
| `Vivo ka 20 piece stock add karo` | Add inventory |
| `Kaun payment nahi kiya` | Overdue customers |
| `Priya ko bill bhejo` | Generate PDF invoice |

---

## 📁 Project Structure

```
Mera-Business/
├── app.py                  # FastAPI server + WhatsApp webhook
├── intent_router.py        # Gemini AI + function calling + context cache
├── simple_intent_router.py # Offline fallback (pattern matching)
├── database.py             # SQLite schema + all DB operations
├── pdf_generator.py        # PDF invoice generation (reportlab)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── Dockerfile              # Container deployment
├── docker-compose.yml      # Docker Compose config
└── README.md               # This file
```

---

## 🔐 Multi-User / Production

The current setup supports **single business owner** (hackathon mode).

For production multi-tenant SaaS:
1. Add `business_owners` table
2. Add `owner_id` FK to all tables
3. Map each WhatsApp business number → `owner_id`
4. Filter all queries with `WHERE owner_id = ?`

See `MULTI_USER_ARCHITECTURE.md` for complete production schema.

---

## 💡 Context Caching

The `system_instruction` and `tools` list are large and identical for every request. We cache them using Gemini's Context Cache API:

```python
cache = client.caches.create(
    model='gemini-2.5-flash',
    config=types.CreateCachedContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOL_LIST,
        ttl=timedelta(hours=1),
    )
)
# Result: $0.03/1M tokens instead of $0.30/1M = 90% savings
```

Falls back gracefully if the prompt is below the 2048-token minimum.

---

## 🏆 Built For

**Neurathon 2026 — PS2: Bharat Biz-Agent**  
AI-powered business management for Indian SMBs via WhatsApp.

---

## 📄 License

MIT License — free to use, modify, and deploy.
