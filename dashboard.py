"""
OPTIONAL Web Dashboard - For Demo/Admin Only
==========================================

⚠️ IMPORTANT: This is NOT the primary interface!
   Users NEVER see this. Everything happens on WhatsApp.
   
   This dashboard is only for:
   - Demo purposes at hackathon
   - Admin viewing data
   - Exporting/backing up data
   
The entire product works 100% through WhatsApp.
This file can be deleted and the product still works perfectly.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import (
    get_daily_summary,
    get_overdue_customers,
    get_low_stock_products
)
import sqlite3
from datetime import datetime

# Import the main app
from app import app

# Simple HTML templates (no complex UI needed - this is optional!)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    """
    Optional admin dashboard - FOR DEMO ONLY
    Users never see this. Everything is on WhatsApp.
    """
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bharat Biz-Agent - Admin Dashboard (DEMO ONLY)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .warning {
            background: #ff4444;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            color: #667eea;
            font-size: 36px;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 16px;
        }
        .whatsapp-demo {
            background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }
        .whatsapp-demo h2 {
            margin-bottom: 15px;
            font-size: 28px;
        }
        .whatsapp-demo .number {
            font-size: 24px;
            font-weight: bold;
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .examples {
            background: #f5f5f5;
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
        }
        .examples h3 {
            color: #333;
            margin-bottom: 20px;
        }
        .example-message {
            background: white;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid #25D366;
        }
        .example-message .user {
            color: #25D366;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .example-message .text {
            color: #333;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 14px;
        }
        .data-link {
            display: inline-block;
            margin: 10px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }
        .data-link:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="warning">
        ⚠️ THIS IS NOT THE USER INTERFACE! Users interact 100% through WhatsApp. This page is ONLY for demo/admin viewing.
    </div>
    
    <div class="container">
        <div class="header">
            <h1>🇮🇳 Bharat Biz-Agent</h1>
            <p>AI-Powered Business Co-Pilot - Neurathon 2026</p>
        </div>

        <div class="whatsapp-demo">
            <h2>📱 Primary Interface: WhatsApp</h2>
            <p>Send messages to your WhatsApp Business number:</p>
            <div class="number">+91-XXXX-XXXX-XXX</div>
            <p style="margin-top: 15px; font-size: 14px; opacity: 0.9;">
                👆 Everything happens here! Voice, text, images - all on WhatsApp
            </p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>STATUS</h3>
                <div class="value">✅ LIVE</div>
                <p style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                    Webhook listening on port 8000
                </p>
            </div>
            <div class="stat-card">
                <h3>DATABASE</h3>
                <div class="value">READY</div>
                <p style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                    SQLite initialized with sample data
                </p>
            </div>
            <div class="stat-card">
                <h3>AI ENGINE</h3>
                <div class="value">ACTIVE</div>
                <p style="font-size: 12px; opacity: 0.8; margin-top: 10px;">
                    Gemini 2.0 Flash with function calling
                </p>
            </div>
        </div>

        <div class="examples">
            <h3>💬 Example WhatsApp Commands</h3>
            
            <div class="example-message">
                <div class="user">You (Voice/Text):</div>
                <div class="text">"Ramesh ko Vivo V29 becha 29999 mein"</div>
            </div>
            <div class="example-message">
                <div class="user">Agent:</div>
                <div class="text">✅ Invoice created! INV20260202001<br>Customer: Ramesh | Amount: ₹35,398.82 (with GST)<br>Stock updated: 49 units remaining</div>
            </div>

            <div class="example-message">
                <div class="user">You:</div>
                <div class="text">"Suresh se 5000 payment aaya UPI se"</div>
            </div>
            <div class="example-message">
                <div class="user">Agent:</div>
                <div class="text">✅ Payment recorded! ₹5,000 via UPI<br>Suresh's balance: ₹15,000 remaining</div>
            </div>

            <div class="example-message">
                <div class="user">You (Voice):</div>
                <div class="text">"आज का हिसाब बताओ"</div>
            </div>
            <div class="example-message">
                <div class="user">Agent:</div>
                <div class="text">📊 आज का हिसाब (02/02/2026)<br>💰 Sales: 3 invoices - ₹89,997<br>💸 Payments: ₹20,000<br>📉 Expenses: ₹5,000<br>💵 Net Cash: +₹15,000</div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <h3 style="margin-bottom: 15px; color: #333;">Optional Admin Data Views</h3>
            <a href="/api/data/summary" class="data-link">View Daily Summary</a>
            <a href="/api/data/pending" class="data-link">Pending Payments</a>
            <a href="/api/data/inventory" class="data-link">Low Stock Alert</a>
        </div>

        <div class="footer">
            <p><strong>Remember:</strong> Users never see this page. They only use WhatsApp! 📱</p>
            <p style="margin-top: 10px;">This dashboard is optional for demo/admin purposes only.</p>
            <p style="margin-top: 20px; font-size: 12px;">
                Built for Neurathon 2026 | Team: [Your Team Name]
            </p>
        </div>
    </div>
</body>
</html>
    """)


@app.get("/api/data/summary")
async def get_summary_data():
    """Optional API endpoint - for demo viewing only"""
    summary = get_daily_summary()
    return {
        "note": "This data is already sent to users via WhatsApp. This API is just for demo viewing.",
        "data": summary
    }


@app.get("/api/data/pending")
async def get_pending_data():
    """Optional API endpoint - for demo viewing only"""
    overdue = get_overdue_customers(days=30)
    return {
        "note": "Users get these reminders automatically on WhatsApp. This is just for demo viewing.",
        "data": overdue
    }


@app.get("/api/data/inventory")
async def get_inventory_data():
    """Optional API endpoint - for demo viewing only"""
    low_stock = get_low_stock_products()
    return {
        "note": "Users get stock alerts on WhatsApp. This is just for demo viewing.",
        "data": low_stock
    }
