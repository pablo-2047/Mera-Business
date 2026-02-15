# 🇮🇳 Bharat Biz-Agent
## AI-Powered Business Co-Pilot for Indian SMBs

**Neurathon 2026 - Problem Statement 2**  
**Team**: [Your Team Name]  
**Date**: February 2, 2026

---

## 📋 Executive Summary

**Problem**: 60+ million Indian SMBs struggle with digital fragmentation, language barriers, and operational friction that drains productivity.

**Solution**: An autonomous WhatsApp-based AI agent that executes real business tasks through conversational Hindi/Hinglish commands.

**Impact**: Reduces "life admin" time by 60%, enabling SMB owners to focus on growth instead of paperwork.

---

## 🎯 The Problem: Digital Divide in Bharat

### Current Reality for Indian SMB Owners

**1. Tool Fatigue Wall**
- WhatsApp for orders
- Tally for accounting  
- Excel for inventory
- Manual, error-prone data entry between systems
- **Result**: 3-4 hours daily wasted on admin tasks

**2. Language & Interface Barriers**
- Most SaaS tools are "English-First"
- Desktop-centric dashboards
- No support for Hindi/Hinglish
- **Result**: Low adoption, high abandonment

**3. Operational Bottlenecks**
- Untracked udhaar (credit) ledgers → revenue leakage
- Manual UPI screenshot reconciliation
- GST compliance anxiety
- **Result**: Cognitive overload, missed growth opportunities

---

## 💡 Our Solution: The Bharat Biz-Agent

### What Makes Us Different

**Not a Chatbot - An Agentic AI**

| Traditional Chatbots | Bharat Biz-Agent |
|---------------------|------------------|
| "Let me help you understand..." | "Done! Invoice created." |
| Provides advice | Executes actions |
| English-only | Hindi/Hinglish/English |
| Requires training | Zero-training interface |
| Desktop apps | WhatsApp-first |

### Core Philosophy

> "Move from 'Receiving Order' to 'Logged in System' with ZERO manual steps"

---

## 🏗️ Technical Architecture

### System Design

```
User → WhatsApp → FastAPI Webhook → Message Buffer
                                          ↓
                              Gemini 2.0 Flash (Intent Router)
                                          ↓
                              Function Calling → Python Executor
                                          ↓
                                    SQLite Database
```

### Key Components

**1. WhatsApp Gateway** (app.py)
- Meta Cloud API webhook
- Message buffering (text + media merge)
- 2-second smart buffer for multi-part messages
- Media download and processing

**2. Intent Router** (intent_router.py)
- Gemini 2.0 Flash with function calling
- Understands Hindi/Hinglish code-mixing
- Maps intent → Python function
- Multimodal: text + voice + image

**3. Function Executor** (database.py)
- Direct SQLite operations
- Inventory management
- Invoice generation
- Payment tracking
- GST compliance
- Udhaar ledger

---

## ✨ Feature Showcase

### 1. Invoice Creation (Sale)

**User Input** (Voice/Text):
```
"Ramesh ko Vivo V29 becha 29999 mein"
```

**Agent Action**:
- Creates invoice with GST calculation
- Updates inventory (stock - 1)
- Generates invoice number
- Sends confirmation to WhatsApp

**Database Operations** (< 100ms):
```sql
INSERT INTO invoices (customer, total, gst)
UPDATE products SET stock = stock - 1
INSERT INTO activity_log
```

### 2. Payment Recording

**User Input**:
```
"Suresh se 5000 payment aaya UPI se, UTR 123456789"
```

**Agent Action**:
- Records payment
- Updates customer outstanding
- Links to specific invoice
- Updates udhaar ledger

### 3. Intelligent Reminders

**Proactive Agent**:
```
"Ramesh का payment 30 दिन से pending है। 
Outstanding: ₹29,999. 
WhatsApp reminder भेजूं?"
```

User: "हां"

Agent: Sends templated reminder via WhatsApp

### 4. Voice-First Interface

**User**: Sends voice note in Hindi
```
"आज का हिसाब बताओ"
```

**Agent**: Transcribes + processes
```
📊 Today's Summary (02/02/2026)

💰 Sales: 3 invoices - ₹89,997
💸 Payments: 2 received - ₹20,000
📉 Expenses: 1 - ₹5,000
💵 Net Cash: +₹15,000
⚠️ Outstanding: ₹54,997
```

### 5. Image Processing

**User**: Sends photo of handwritten bill

**Agent**: 
- OCR extraction
- Structured data creation
- Invoice generation
- Confirmation with editable details

---

## 🇮🇳 India-First Engineering

### Multilingual NLP

**Code-Mixing Support**:
```
"Kal payment bhej dena" ✓
"कल मुझे याद दिला देना" ✓  
"Tomorrow remind me" ✓
"Aaj ka hisaab kitna hua?" ✓
```

**Regional Context Understanding**:
- "बेचा" = sold
- "उधार" = credit sale
- "पैसे आए" = payment received
- "हिसाब" = accounts/ledger

### GST Compliance

**Automatic GST Calculation**:
- 5% (essential goods)
- 12% (standard goods)
- 18% (electronics - default)
- 28% (luxury goods)

**GST-Compliant Invoicing**:
- HSN codes
- GSTIN validation
- Monthly filing summaries

### UPI Integration Ready

**Planned Features**:
- UPI screenshot → automatic reconciliation
- Payment link generation
- Razorpay/PhonePe integration

---


