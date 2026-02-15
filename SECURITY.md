# 🔐 Security Guide: Protecting Your API Keys

## Overview

This guide explains how to securely handle sensitive information (like API keys) in your application, especially for hackathon demonstrations.

---

## 🚨 The Problem

**Never commit secrets to Git!**

Bad ❌:
```bash
# .env file committed to GitHub
GEMINI_API_KEY=AIzaSyDv9zwd2Qo6yCdQu60R_SbV7WhFzJ5uzUM
```

Anyone can see your API key and abuse it!

---

## ✅ Solution 1: Environment Variables (Recommended for Hackathons)

### Step 1: Use `.env.example` as Template

```bash
# .env.example (committed to Git)
GEMINI_API_KEY=your_key_here
BUSINESS_NAME=Your Business Name
```

### Step 2: Create Actual `.env` File Locally

```bash
# Copy template
cp .env.example .env

# Edit with real values
nano .env

# Add .env to .gitignore
echo ".env" >> .gitignore
```

### Step 3: Docker Reads from `.env`

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

**Judges workflow:**
1. Clone your repo
2. Create `.env` file with their own key
3. Run `docker-compose up`

✅ **Pros:** Simple, standard practice  
❌ **Cons:** Judges need their own API key

---

## 🎯 Solution 2: Pre-configured Demo (For Judges)

For hackathons, you want judges to test quickly without setup hassle.

### Option A: Temporary API Key

Create a **temporary key** just for judging:

```bash
# 1. Go to https://aistudio.google.com/app/apikey
# 2. Create new key: "Neurathon-2026-Demo"
# 3. Set quota limits (e.g., 100 requests/day)
# 4. Include in .env.example

# .env.example
GEMINI_API_KEY=AIzaSyDEMO_KEY_FOR_JUDGING_ONLY
# NOTE: This is a temporary key for evaluation
# Will be revoked after judging period
```

✅ **Pros:** Zero friction for judges  
⚠️ **Cons:** Key is visible in repo  
✅ **Mitigation:** Delete key after hackathon

### Option B: Docker Secrets (Production-Grade)

For production or if you want to hide the key even from judges:

#### Step 1: Create Secrets Directory

```bash
mkdir secrets
echo "your_actual_gemini_key" > secrets/gemini_key.txt
echo "secrets/" >> .gitignore
```

#### Step 2: Use Docker Secrets

```yaml
# docker-compose.secrets.yml
version: '3.8'

services:
  mera-business:
    build: .
    ports:
      - "8000:8000"
    secrets:
      - gemini_api_key
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key

secrets:
  gemini_api_key:
    file: ./secrets/gemini_key.txt
```

#### Step 3: Update Code to Read Secret

```python
# app.py or config.py
import os

def get_gemini_key():
    """Read API key from Docker secret or environment variable"""
    # Try Docker secret first
    secret_file = os.getenv('GEMINI_API_KEY_FILE')
    if secret_file and os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    # Fallback to environment variable
    return os.getenv('GEMINI_API_KEY')

GEMINI_API_KEY = get_gemini_key()
```

#### For Judges:

```bash
# You provide them with secrets/ folder separately
# (e.g., USB drive, private link, email)

# 1. Clone repo
git clone https://github.com/your-repo/mera-business.git

# 2. Copy secrets folder (you provide)
cp -r /path/to/secrets ./secrets/

# 3. Run with secrets
docker-compose -f docker-compose.secrets.yml up
```

✅ **Pros:** Key completely hidden from repo  
❌ **Cons:** Extra step for judges (need secrets folder)

---

## 🏆 Solution 3: Cloud Deployment (Best for Hackathons)

Deploy to cloud platform with key already configured.

### Railway Deployment

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login and initialize
railway login
railway init

# 3. Add environment variable
railway variables set GEMINI_API_KEY=your_key_here

# 4. Deploy
railway up
```

**For judges:** Just visit the URL (e.g., `https://mera-business.up.railway.app/chat`)

✅ **Pros:** Best user experience, professional  
✅ **Pros:** Key never exposed  
❌ **Cons:** Requires Railway account (free tier available)

---

## 🎯 Recommended Strategy for Neurathon 2026

### Primary Approach: Cloud + Docker Fallback

```
1. CLOUD DEMO (Primary)
   - Deploy to Railway/Render
   - Include URL in README
   - Judges test in 10 seconds

2. DOCKER FALLBACK (Backup)
   - Include .env.example
   - Provide temporary demo key OR
   - Let judges use their own key
```

### What to Include in GitHub:

✅ **Include:**
- `.env.example` (template with placeholder keys)
- `docker-compose.yml` (reads from `.env`)
- Clear README with setup instructions
- SECURITY.md (this file)

❌ **Never Include:**
- `.env` (actual keys)
- `secrets/` directory
- Any file with real API keys

### `.gitignore` Setup:

```gitignore
# Secrets
.env
.env.*
!.env.example
secrets/

# API Keys
*_key.txt
*_secret.txt
credentials.json
```

---

## 📋 Checklist Before Pushing to GitHub

Before `git push`, verify:

- [ ] No `.env` file in repo
- [ ] `.env.example` has placeholders only
- [ ] `.gitignore` includes `.env` and `secrets/`
- [ ] No hardcoded keys in Python files
- [ ] Docker secrets stored separately
- [ ] README explains how judges get keys

### Quick Check:

```bash
# Search for potential secrets
git grep -i "api.*key" *.py *.yml *.json

# Check what will be committed
git status
git diff --cached

# Verify .gitignore is working
git check-ignore .env
# Should output: .env
```

---

## 🔒 Best Practices Summary

### For Development:
1. Use `.env` file (never commit)
2. Use `.env.example` as template
3. Load with `python-dotenv`

### For Docker:
1. Pass via environment variables
2. Or use Docker secrets for production
3. Mount `.env` as volume (optional)

### For Hackathon Demo:
1. Deploy to cloud (Railway/Render)
2. Provide live URL with key pre-configured
3. Offer Docker alternative with instructions

### For Production:
1. Use secrets management (AWS Secrets Manager, HashiCorp Vault)
2. Rotate keys regularly
3. Monitor usage and set quotas
4. Use separate keys for dev/staging/prod

---

## 🚀 Example: Complete Setup for Judges

### File: `.env.example`
```bash
# Mera Business Configuration
# Copy this file to .env and fill in your values

# Required: Get free key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For WhatsApp integration
WHATSAPP_TOKEN=your_whatsapp_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here

# Business Details (for invoice generation)
BUSINESS_NAME=Your Shop Name
BUSINESS_ADDRESS=Your Address
BUSINESS_GSTIN=YOUR_GSTIN_HERE
```

### File: `README.md` (excerpt)
```markdown
## 🚀 Quick Start

### For Judges (Fastest Way):

**Option 1: Live Demo (Recommended)**
Visit: https://mera-business-demo.up.railway.app/chat
- No setup required
- Pre-loaded with sample data
- Ready to test immediately

**Option 2: Docker (Local Testing)**
```bash
# 1. Clone repository
git clone https://github.com/pablo-2047/Mera-Business.git
cd Mera-Business

# 2. Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
# Get free key: https://aistudio.google.com/app/apikey

# 3. Run
docker-compose up

# 4. Visit http://localhost:8000/chat
```

### API Key Setup:
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy key and paste in `.env` file
4. Save and run `docker-compose up`
```

---

## 🛡️ Security Incident Response

If you accidentally commit a secret:

### Immediate Actions:

```bash
# 1. Revoke the key immediately
# Go to Google AI Studio → Delete the key

# 2. Remove from Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push (destructive!)
git push origin --force --all

# 4. Create new key
# Get new key from Google AI Studio

# 5. Update .env locally
echo "GEMINI_API_KEY=new_key_here" > .env
```

### Prevention:
- Use pre-commit hooks
- Use `git-secrets` tool
- Review diffs before committing

---

## 📚 Additional Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [12-Factor App Config](https://12factor.net/config)

---

## ✅ Final Recommendation

**For Neurathon 2026 Submission:**

1. ✅ Deploy to Railway with key configured
2. ✅ Include `.env.example` in GitHub
3. ✅ Add clear setup instructions in README
4. ✅ Mention cloud demo as primary option
5. ✅ Provide Docker as backup with instructions

**This gives judges:**
- Instant testing (cloud demo)
- Flexibility (Docker local)
- Security (no keys in repo)
- Professional presentation

---

<div align="center">

**Security First, Innovation Always** 🔒

</div>
