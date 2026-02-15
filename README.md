<div align="center">

# 🇮🇳 Mera Business

### WhatsApp AI Agent for Indian Small Businesses

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud_API-25D366?logo=whatsapp&logoColor=white)](https://developers.facebook.com/docs/whatsapp)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Invoice creation. Payment tracking. Inventory management.**  
**All through WhatsApp. In Hindi, Hinglish, or English.**

*Built for Neurathon 2026 — PS2: Bharat Biz-Agent*

</div>

---

## The Problem

India has **60+ million small shop owners**. They manage invoices on paper, track payments in notebooks, and lose thousands every month to untracked credit (udhaar). Most business software is English-first, desktop-first, and requires training they don't have time for.

**Mera Business** puts an AI business assistant directly in their WhatsApp — the app they already use all day.

---

## How It Works

```
Your WhatsApp  ──▶  Meta Cloud API  ──▶  FastAPI Server  ──▶  Gemini 2.5 Flash  ──▶  SQLite DB
                                                                      │
                                                              Understands Hindi /
                                                              Hinglish / English
                                                              Calls DB functions
                                                              Replies naturally
```

You send a message. The AI understands it, executes the right database operation, and replies — all within seconds.

---

## Demo

```
You:    "Ramesh ko Vivo V29 becha 29999 mein"

Agent:  ✅ Invoice created!
        📄 INV20260214-0042
        👤 Ramesh Kumar
        📦 Vivo V29 × 1
        💰 ₹29,999 + GST ₹5,400 = ₹35,399
        📦 Stock: 49 units remaining
```

```
You:    "Aaj ka hisaab batao"

Agent:  📊 Today's Summary — 14/02/2026
        💰 Sales   : 3 invoices  — ₹1,05,000
        💸 Payments: 2 received  — ₹75,000
        ⚠️  Udhaar  : ₹30,000 outstanding
        💵 Net Cash: ₹75,000
```

```
You:    "Suresh se 30000 payment aaya UPI se, UTR 123456789012"

Agent:  ✅ Payment recorded!
        👤 Suresh
        💰 ₹30,000 via UPI
        🔖 UTR: 123456789012
        📊 Outstanding: ₹0
```

---

## Features

| | Feature | Description |
|---|---------|-------------|
| 🧾 | **Invoice Creation** | Sell something in one line — GST calculated automatically |
| 💰 | **Payment Tracking** | Record UPI/cash payments with UTR numbers |
| 📦 | **Inventory Management** | Real-time stock updates, low-stock alerts |
| 👥 | **Customer Ledger** | Udhaar tracking per customer, overdue reminders |
| 📊 | **Daily Summary** | Full P&L snapshot with one message |
| 📄 | **PDF Invoices** | Professional GST-compliant PDF generation |
| 🎤 | **Voice Messages** | Send a voice note — agent transcribes and acts |
| 🌐 | **Multilingual** | Hindi, Hinglish, English — auto-detected |
| ⚡ | **Context Caching** | 90% API cost reduction via Gemini cache |
| 🔄 | **Offline Fallback** | Pattern-matching router works even if AI API is down |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Gemini API Key](https://aistudio.google.com/app/apikey) — free
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/) — free tier: 1,000 msgs/month
- [ngrok](https://ngrok.com) for local webhook tunnelling

### 1. Clone & setup

```bash
git clone https://github.com/pablo-2047/Mera-Business.git
cd Mera-Business

python -m venv venv
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows

python setup.py               # installs deps + initialises DB + adds sample data
```

### 2. Configure

```bash
# setup.py creates .env from .env.example automatically
# Just fill in your keys:
nano .env     # or open in any editor
```

```env
WHATSAPP_VERIFY_TOKEN=any_secret_string_you_choose
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=12345678901234
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
BUSINESS_OWNER_PHONE=+91XXXXXXXXXX
```

### 3. Run

```bash
# Terminal 1 — start the server
uvicorn app:app --reload --port 8000

# Terminal 2 — expose it to the internet
ngrok http 8000
```

### 4. Connect WhatsApp

1. Copy your ngrok URL (e.g. `https://abc123.ngrok-free.app`)
2. In [Meta Developer Console](https://developers.facebook.com) → WhatsApp → Configuration
3. Set webhook: `https://abc123.ngrok-free.app/webhook`
4. Verify token: matches `WHATSAPP_VERIFY_TOKEN` in your `.env`
5. Subscribe to: `messages`
6. Add your phone number to the test number list
7. Send a WhatsApp message and watch it work

---

## Command Reference

| Say this... | What happens |
|-------------|-------------|
| `Ramesh ko Vivo becha 29999` | Creates invoice |
| `Suresh ko phone udhaar pe diya` | Creates credit sale (no payment) |
| `Ramesh se 5000 payment aaya UPI se` | Records payment |
| `Aaj ka hisaab batao` | Daily P&L summary |
| `Samsung ka stock kitna hai` | Stock check |
| `Vivo ka 20 piece stock add karo` | Add inventory |
| `Kaun payment nahi kiya` | Lists overdue customers |
| `Priya ka invoice banao` | Generate PDF invoice |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  app.py  —  FastAPI webhook server                           │
│  • Verifies Meta webhook handshake                           │
│  • Buffers text + media (2 sec window) into one AI call     │
│  • Checks phone whitelist before processing                  │
│  • Downloads voice/image from WhatsApp CDN                   │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│  intent_router.py  —  Gemini 2.5 Flash                       │
│  • Context Cache: system prompt + tools cached 1 hr          │
│    (saves 90% on input token costs)                          │
│  • Function calling: AI picks the right DB function          │
│  • Two-turn: executes function, feeds result back for reply  │
│  • Falls back to simple_intent_router on any API error       │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│  database.py  —  SQLite (WAL mode)                           │
│  Tables: products · customers · invoices · invoice_items     │
│          payments · expenses · udhaar_ledger · gst_filings   │
│          activity_log                                         │
└──────────────────────────────────────────────────────────────┘
```

### Why SQLite?

Perfect for Indian SMB deployments: zero server setup, file-based backups, sub-100ms queries, works on ₹500/month VPS, offline-capable. Easily upgraded to PostgreSQL when you need multi-tenant scale.

### Context Caching

Every request sends the same large `system_instruction` + 8-function `tools` list. Gemini's Context Cache stores this for 1 hour — the cached tokens cost **$0.025/1M** vs **$0.30/1M** uncached. For 1,000 messages/day that's ~₹500/month saved.

```python
cache = client.caches.create(
    model='gemini-2.5-flash',
    config=types.CreateCachedContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOL_LIST,
        ttl=timedelta(hours=1),
    )
)
```

---

## Project Structure

```
Mera-Business/
├── app.py                   # FastAPI server + WhatsApp webhook handler
├── intent_router.py         # Gemini AI + function calling + context cache
├── simple_intent_router.py  # Offline fallback (regex pattern matching)
├── database.py              # SQLite schema + all business logic functions
├── pdf_generator.py         # Professional PDF invoice generation
├── dashboard.py             # Optional web admin dashboard (demo use)
├── setup.py                 # One-command setup script
├── requirements.txt         # Python dependencies (pinned versions)
├── .env.example             # Environment variable template
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Docker Compose
├── README.md                # This file
├── DEPLOYMENT.md            # Full deployment guide (Railway/Render/AWS)
├── QUICKSTART.md            # 5-minute setup guide
└── MULTI_USER_ARCHITECTURE.md  # Production multi-tenant design
```

> **venv/** and **.env** are in `.gitignore` — never committed.  
> **venv** contains thousands of binary files specific to your OS — others run `pip install -r requirements.txt` to get their own. **Never push venv to GitHub.**

---

## Deployment

### Railway (recommended for demo — free)

```bash
# 1. Push to GitHub (already done)
# 2. railway.app → New Project → Deploy from GitHub
# 3. Add env vars in Railway dashboard
# 4. Deploy — get HTTPS URL automatically
# 5. Update WhatsApp webhook to Railway URL
```

### Docker

```bash
docker compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for Render, Heroku, AWS EC2, and DigitalOcean guides.

---

## Roadmap

- [x] WhatsApp webhook integration
- [x] Gemini 2.5 Flash with function calling
- [x] Context Caching (90% cost reduction)
- [x] Hindi / Hinglish / English NLP
- [x] Invoice, payment, inventory, udhaar
- [x] PDF invoice generation
- [x] Voice message support
- [x] Offline fallback router
- [ ] Image OCR (handwritten bill scanning)
- [ ] UPI payment link generation
- [ ] Scheduled udhaar reminders
- [ ] Tally ERP sync
- [ ] Multi-tenant / SaaS mode

---

## FAQ

**Do I need to download any app?**  
No. Users only need WhatsApp, which they already have.

**Does it work offline?**  
The pattern-matching fallback router works without any API calls. The AI router needs internet.

**Can I push venv to GitHub?**  
No — and you shouldn't. venv contains OS-specific binaries (thousands of files, 100+ MB). Everyone who clones the repo runs `pip install -r requirements.txt` to get their own. That's what `requirements.txt` is for.

**Is my .env safe?**  
`.env` is in `.gitignore` so git never tracks it. Only `.env.example` (with placeholder values) is committed.

---

## License

MIT — free to use, fork, and deploy commercially.

---

<div align="center">
Built with ❤️ for India's 60 million shop owners
</div>
