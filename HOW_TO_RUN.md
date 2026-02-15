# 🎯 How to Run Mera Business — Step by Step Guide

This guide helps you get the application running quickly, whether using Docker or local Python.

---

## 🚀 Method 1: Docker (Recommended — Easiest)

**Time required:** 3-5 minutes

### Prerequisites

- Docker Desktop installed
  - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Linux: Install docker and docker-compose
- 2GB free disk space
- Internet connection (for first-time setup)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/pablo-2047/Mera-Business.git
   cd Mera-Business
   ```

2. **Create environment file**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env file (use any text editor)
   # Windows: notepad .env
   # Mac/Linux: nano .env
   
   # Add your Gemini API key:
   GEMINI_API_KEY=your_actual_key_here
   ```
   
   **Get FREE API key:** https://aistudio.google.com/app/apikey

3. **Start with Docker**
   ```bash
   docker-compose up
   ```
   
   Wait for the message: `Application startup complete`

4. **Open in browser**
   - Chat UI: http://localhost:8000/chat
   - Dashboard: http://localhost:8000

5. **Test the application**
   Type in chat: `"Ramesh ko iPhone becha 79999"`

6. **Stop the application**
   - Press `Ctrl + C` in terminal
   - Or run: `docker-compose down`

---

## 💻 Method 2: Local Python

**Time required:** 5-10 minutes

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- 500MB free disk space
- Internet connection

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/pablo-2047/Mera-Business.git
   cd Mera-Business
   ```

2. **Create virtual environment**
   ```bash
   # Create venv
   python -m venv venv
   
   # Activate
   # Windows:
   venv\Scripts\activate
   
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit with your API key
   # Windows: notepad .env
   # Mac/Linux: nano .env
   ```

5. **Generate sample data**
   ```bash
   python generate_sample_data.py
   ```

6. **Run application**
   ```bash
   python app.py
   ```

7. **Open in browser**
   - Chat UI: http://localhost:8000/chat
   - Dashboard: http://localhost:8000

8. **Stop the application**
   - Press `Ctrl + C` in terminal

---

## 🎮 How to Test

### Test Commands (Copy-paste into chat)

#### 1. Create Invoice (Hindi/Hinglish)
```
Ramesh ko iPhone becha 79999
```
**Expected:** Invoice created with GST calculation, warranty tracked

#### 2. Record Payment
```
Ramesh se 20000 payment aaya UPI se
```
**Expected:** Payment recorded, balance updated

#### 3. Check Summary
```
Aaj ka hisaab batao
```
**Expected:** Daily sales, payments, expenses shown

#### 4. Check Warranty
```
Ramesh ka warranty check karo
```
**Expected:** List of products with warranty details

#### 5. Manage Inventory
```
Samsung ka 10 units stock add karo
```
**Expected:** Stock updated, confirmation shown

#### 6. Check Udhaar (Credit)
```
Kitne customers ka payment pending hai?
```
**Expected:** List of customers with outstanding balances

#### 7. Low Stock Alert
```
Low stock products dikhao
```
**Expected:** Products below stock threshold

---

## 🔍 What to Look For

### ✅ Multilingual Support
Try commands in:
- **Hindi:** "रमेश को फोन बेचा तीस हजार"
- **Hinglish:** "Ramesh ko phone becha 30000"
- **English:** "Sold phone to Ramesh for 30000"

All should work!

### ✅ Agentic AI (Actually Does Things)
- Creates invoices in database
- Generates PDF receipts (check `/invoices` folder)
- Updates inventory automatically
- Tracks warranties with expiry dates
- Calculates GST correctly

### ✅ Context Awareness
```
You: "Ramesh ka pending kitna hai?"
AI: "₹45,000 outstanding"

You: "Reminder bhejo"
AI: [Prepares reminder with details]
```

### ✅ India-First Features
- GST calculation (18%)
- UPI/Cash payment tracking
- Udhaar (informal credit) management
- Hindi/Hinglish native support
- Mobile-first design

---

## 📊 Pre-loaded Demo Data

The application comes with realistic test data:

### Products (26 items)
- iPhone 15: ₹79,999 (12-month warranty)
- Samsung S23: ₹54,999 (24-month warranty)
- Vivo V29: ₹29,999 (12-month warranty)
- OnePlus, Xiaomi, tablets, laptops, accessories

### Customers (10 people)
- Ramesh Kumar: +919876543210
- Suresh Gupta: +919876543211
- Priya Sharma: +919876543212
- And 7 more...

### Sample Invoices
- Recent paid invoices (for analytics)
- Pending udhaar invoices (for testing)
- Warranty tracking enabled

---

## 🐛 Troubleshooting

### Issue: Port 8000 already in use

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9

# Then restart application
```

### Issue: Docker build fails

**Solution:**
```bash
# Clean build
docker-compose down
docker system prune -a
docker-compose up --build
```

### Issue: Database locked error

**Solution:**
```bash
# Stop all processes
docker-compose down

# Remove old database (will regenerate)
rm bharat_biz.db

# Restart
docker-compose up
```

### Issue: Gemini API error

**Check:**
1. Is `GEMINI_API_KEY` set in `.env`?
2. Is the key valid? (Test at https://aistudio.google.com)
3. Did you restart the application after editing `.env`?

**Test API key manually:**
```bash
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Issue: Application starts but chat doesn't work

**Check:**
1. Visit http://localhost:8000/health (should return `{"status":"healthy"}`)
2. Open browser console (F12) for errors
3. Check terminal for Python errors

### Issue: Sample data not showing

**Regenerate:**
```bash
# Stop application (Ctrl+C)

# Delete database
rm bharat_biz.db

# Regenerate
python generate_sample_data.py

# Restart
python app.py
```

---

## 📱 Mobile Testing

The application is mobile-responsive. To test on mobile:

1. Find your computer's IP address
   ```bash
   # Windows
   ipconfig
   
   # Mac/Linux
   ifconfig
   ```

2. Visit on mobile browser:
   ```
   http://<your-ip>:8000/chat
   ```

3. Test voice input (click mic icon)

---

## 🎯 Performance Benchmarks

What to expect:

| Metric | Target | Typical |
|--------|--------|---------|
| Initial load | < 2s | ~1s |
| AI response | < 3s | ~1.5s |
| Database query | < 100ms | ~50ms |
| PDF generation | < 2s | ~1s |

---

## 📹 Video Guide

[Link to video demonstration] (Coming soon)

Shows:
- Installation process
- Docker setup
- Testing all features
- Common issues and fixes

---

## 💡 Tips for Best Experience

1. **Use Chrome or Firefox** for best compatibility
2. **Try voice input** (mobile or desktop with mic)
3. **Test all languages** (Hindi, Hinglish, English)
4. **Check the dashboard** for analytics visualization
5. **Look in `/invoices`** folder for generated PDFs
6. **Try edge cases** (negative amounts, invalid names, etc.)

---

## 🆘 Need Help?

### Quick Fixes

**Application won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Docker issues:**
```bash
# Restart Docker Desktop
# Then try again
docker-compose up --build
```

**API key problems:**
```bash
# Verify .env file
cat .env | grep GEMINI_API_KEY

# Should show: GEMINI_API_KEY=AIzaSy...
```

### Still Stuck?

1. Check GitHub Issues: [Link to issues page]
2. Read TROUBLESHOOTING.md (if available)
3. Review logs: `docker-compose logs` or check terminal output

---

## ✅ Success Indicators

You know it's working when:

- ✅ http://localhost:8000/chat loads
- ✅ You can type a message and get a response
- ✅ Commands in Hindi/Hinglish work
- ✅ Invoices are created (check dashboard)
- ✅ PDF files appear in `/invoices` folder
- ✅ No error messages in terminal

---

## 🎉 You're All Set!

Application is now running. Try the test commands above and explore the features!

**Happy testing!** 🚀

---

<div align="center">

**Need more help?** Check the full README.md for detailed documentation.

</div>
