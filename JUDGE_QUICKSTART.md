# 🎯 Quick Start Guide for Judges — Neurathon 2026

**Testing "Mera Business" AI Agent in 3 Minutes**

---

## 🚀 Fastest Way: Docker (Recommended)

### Prerequisites
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- 5 minutes of your time

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/pablo-2047/Mera-Business.git
cd Mera-Business

# 2. Create environment file (use our provided API key for testing)
cp .env.example .env

# 3. Start the application
docker-compose up

# Wait for: "Application startup complete" message

# 4. Open your browser
# Visit: http://localhost:8000/chat
```

That's it! The application is now running with pre-loaded demo data.

---

## 🧪 Test Commands

Try these in the chat interface:

### Invoice Creation (Hindi/Hinglish)
```
"Ramesh ko iPhone becha 79999"
"Suresh ko Samsung S23 becha 54999"
```

### Check Business Summary
```
"Aaj ka hisaab batao"
"Daily summary"
```

### Payment Recording
```
"Ramesh se 20000 payment aaya UPI se"
"Suresh ne 10000 diye cash mein"
```

### Warranty Check
```
"Ramesh ka warranty check karo"
"Warranty status for Ramesh Kumar"
```

### Inventory Management
```
"Samsung ka 10 units stock add karo"
"Low stock products dikhao"
```

### Udhaar (Credit) Tracking
```
"Kon se customers ka payment pending hai?"
"Overdue customers"
```

---

## 📊 What to Look For

### 1. Multilingual Understanding ✅
The AI understands:
- **Hindi:** "रमेश को फोन बेचा"
- **Hinglish:** "Ramesh ko phone becha 30000"  
- **English:** "Sold phone to Ramesh for 30000"

### 2. Agentic AI (Takes Action) ✅
Not just a chatbot — it actually:
- Creates invoices in database
- Generates PDF receipts
- Updates inventory
- Tracks warranties
- Calculates GST automatically

### 3. Context Awareness ✅
Remembers conversation:
```
You: "Ramesh ka pending kitna hai?"
AI: "₹45,000 outstanding"

You: "Reminder bhejo"
AI: [Prepares WhatsApp reminder]
```

### 4. India-First Features ✅
- GST calculation (18%)
- UPI payment tracking
- Udhaar (informal credit) management
- Hindi/Hinglish native support

---

## 🎨 User Interface Tour

### Chat Interface (`/chat`)
- WhatsApp-like design
- Voice input support (click mic icon)
- Real-time responses
- Media upload capability

### Dashboard (`/`)
- Sales analytics
- Inventory alerts
- Udhaar tracking
- Weekly performance charts

---

## 🔍 Evaluation Criteria Checklist

| Criteria | Weight | Evidence in Demo |
|----------|--------|------------------|
| **Industry Relevance** | 30% | Retail/SMB focus, real business workflows |
| **India-First Engineering** | 25% | Hindi/Hinglish NLP, GST, Udhaar tracking |
| **Actionability (Agentic AI)** | 20% | Creates invoices, updates DB, generates PDFs |
| **Integration Complexity** | 15% | Chat → Gemini → Database → PDF pipeline |
| **Trust & Safety** | 10% | Input validation, error handling, audit logs |

---

## 🐳 Alternative: Docker with Your Own API Key

If you want to test with your own Gemini API key:

```bash
# 1. Get free API key from:
# https://aistudio.google.com/app/apikey

# 2. Edit .env file:
nano .env  # or use any text editor

# 3. Replace this line:
GEMINI_API_KEY=your_key_here

# 4. Restart Docker:
docker-compose down
docker-compose up
```

---

## 🛠️ Without Docker (Local Python)

If Docker is not available:

```bash
# 1. Clone repository
git clone https://github.com/pablo-2047/Mera-Business.git
cd Mera-Business

# 2. Create virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 5. Generate demo data
python generate_sample_data.py

# 6. Run application
python app.py

# 7. Visit http://localhost:8000/chat
```

---

## 📦 Pre-loaded Demo Data

The system comes with realistic test data:

**26 Products:**
- iPhones, Samsung phones, OnePlus, Xiaomi
- Tablets, laptops, wearables, audio devices
- With warranties (6-24 months)

**10 Customers:**
- Ramesh Kumar, Suresh Gupta, Priya Sharma, etc.
- With phone numbers and addresses
- Some with pending payments (Udhaar)

**Sample Invoices:**
- Paid invoices (last 7 days) for analytics
- Udhaar invoices (overdue) for testing reminders
- Warranty tracking enabled

---

## ⚡ Performance Expectations

| Metric | Target | Actual |
|--------|--------|--------|
| AI Response Time | < 2s | ~1.2s avg |
| Page Load | < 1s | ~500ms |
| Concurrent Users | 10+ | Tested 20+ |
| Memory Usage | < 500MB | ~300MB |

---

## 🐛 Troubleshooting

### Issue: Port 8000 already in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue: Database locked
```bash
# Restart Docker
docker-compose down
docker-compose up
```

### Issue: Gemini API error
```bash
# Check if key is set in .env
cat .env | grep GEMINI_API_KEY

# Test key manually:
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## 📱 Testing Scenarios

### Scenario 1: New Sale with Warranty
```
1. "Ramesh ko iPhone 15 becha 79999"
2. Check: Invoice created ✓, Warranty tracked ✓, GST calculated ✓
3. "Ramesh ka warranty dekho"
4. Check: Shows expiry date and remaining days ✓
```

### Scenario 2: Credit Sale (Udhaar)
```
1. "Suresh ko Samsung becha 54999 udhaar mein"
2. Check: Invoice created without payment ✓
3. "Pending payments dikhao"
4. Check: Suresh appears in list ✓
5. "Suresh se 20000 payment aaya"
6. Check: Balance updated ✓
```

### Scenario 3: Inventory Management
```
1. "Low stock products"
2. Check: Lists products below threshold ✓
3. "Vivo ka 20 units add karo"
4. Check: Stock updated in database ✓
```

### Scenario 4: Daily Business Summary
```
1. "Aaj ka hisaab batao"
2. Check: Shows sales count, payment received, expenses, net cash ✓
3. Visit dashboard (http://localhost:8000)
4. Check: Charts showing weekly trends ✓
```

---

## 🎯 Key Differentiators

What makes this solution stand out:

1. **True Agentic AI** — Executes actions, not just answers
2. **Multilingual from Ground Up** — Hindi/Hinglish native support
3. **India-Specific Logic** — GST, Udhaar, UPI built-in
4. **Production-Ready** — Docker, error handling, logging
5. **Zero Training Required** — Natural conversation interface
6. **Offline Fallback** — Pattern matching when AI unavailable

---

## 📹 Demo Video

[Link to demo video showcasing all features] (coming soon)

---

## 📧 Questions or Issues?

- **GitHub Issues:** https://github.com/pablo-2047/Mera-Business/issues
- **Documentation:** See README.md for detailed docs
- **Docker Guide:** See DOCKER_JUDGE_GUIDE.md for advanced setup

---

## ✅ Evaluation Checklist

**Before scoring, please verify:**

- [ ] Can understand Hindi/Hinglish commands
- [ ] Actually creates invoices (not just chat)
- [ ] Generates PDF receipts
- [ ] Tracks GST automatically
- [ ] Manages Udhaar (credit sales)
- [ ] Updates inventory in real-time
- [ ] Tracks product warranties
- [ ] Shows daily business summary
- [ ] Handles edge cases gracefully
- [ ] Works smoothly on mobile browsers

---

<div align="center">

**Thank you for evaluating our project!** 🙏

**Made with ❤️ for Indian SMBs**

</div>
