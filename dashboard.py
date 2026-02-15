"""
Mera Business — Full Bilingual Web Dashboard
Hindi/English toggle, live data, 4 tabs, mobile-friendly, OTP authentication
"""
DEMO_MODE = True
from fastapi import APIRouter, Request, Cookie, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from database import (
    get_daily_summary, get_overdue_customers, get_low_stock_products,
    get_all_products, get_all_customers, get_all_invoices, get_weekly_summary,
    init_database, create_product, update_inventory, get_owner_onboarding_status
)
from datetime import datetime, timedelta
import os
import random
import hashlib

router = APIRouter()

def register_routes(app):
    app.include_router(router)

# Lazy import to avoid circular dependency
def _send_whatsapp_message():
    from app import send_whatsapp_message
    return send_whatsapp_message

# ── OTP Management ────────────────────────────────────────────────────────────
OTP_STORE = {}  # phone -> {'otp_hash': str, 'expires': datetime, 'attempts': int}


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    """Hash OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()


DEMO_MODE = True  # Set False in production to enable OTP login
DEMO_OWNER_ID = "+919999999999"  # Demo owner for hackathon

# ── Authentication Helpers ────────────────────────────────────────────────────
async def get_authenticated_user(request: Request) -> str:
    """Get authenticated user's phone. In demo mode, always returns demo owner."""
    if DEMO_MODE:
        return DEMO_OWNER_ID
    owner_id = request.cookies.get("owner_id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return owner_id


# ── Login Page ────────────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(LOGIN_HTML)


@router.post("/api/send-otp")
async def send_otp(request: Request):
    try:
        data = await request.json()
        phone = data.get('phone', '').strip()
        
        if not phone or not phone.startswith('+91'):
            return JSONResponse({"success": False, "error": "Invalid phone number"})
        
        # Check if user exists
        status = get_owner_onboarding_status(phone)
        
        if not status['exists'] or not status['onboarding_complete']:
            return JSONResponse({
                "success": False, 
                "error": "Please register via WhatsApp first. Send any message to the WhatsApp bot to start."
            })
        
        # Generate 6-digit OTP
        otp = generate_otp()
        
        # Store OTP (expires in 5 minutes)
        OTP_STORE[phone] = {
            'otp_hash': hash_otp(otp),
            'expires': datetime.now() + timedelta(minutes=5),
            'attempts': 0
        }
        
        # Send OTP via WhatsApp
        message = f"""🔐 *Mera Business - Web Login OTP*

Your OTP for dashboard login:

*{otp}*

Valid for 5 minutes.
Do not share this code.

अपना OTP किसी के साथ शेयर न करें।"""
        
        await _send_whatsapp_message()(phone, message)
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": "Server error"})


@router.post("/api/verify-otp")
async def verify_otp(request: Request):
    try:
        data = await request.json()
        phone = data.get('phone', '').strip()
        otp = data.get('otp', '').strip()
        
        if phone not in OTP_STORE:
            return JSONResponse({"success": False, "error": "OTP expired or not found"})
        
        stored = OTP_STORE[phone]
        
        # Check expiry
        if datetime.now() > stored['expires']:
            OTP_STORE.pop(phone)
            return JSONResponse({"success": False, "error": "OTP expired"})
        
        # Check attempts (max 3)
        stored['attempts'] += 1
        if stored['attempts'] > 3:
            OTP_STORE.pop(phone)
            return JSONResponse({"success": False, "error": "Too many attempts. Request new OTP."})
        
        # Verify OTP
        otp_hash = hash_otp(otp)
        if otp_hash != stored['otp_hash']:
            return JSONResponse({"success": False, "error": "Invalid OTP"})
        
        # OTP verified! Create session
        OTP_STORE.pop(phone)
        
        response = JSONResponse({"success": True, "redirect": "/"})
        
        # Set secure session cookie
        response.set_cookie(
            key="owner_id",
            value=phone,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        return JSONResponse({"success": False, "error": "Verification failed"})


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("owner_id")
    return response


# ── Dashboard (Protected) ─────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Skip auth check in demo mode
    if not DEMO_MODE:
        owner_id = request.cookies.get("owner_id")
        if not owner_id:
            return RedirectResponse(url="/login")
    return HTMLResponse(DASHBOARD_HTML)

@router.get("/api/summary")
async def api_summary(request: Request):
    owner_id = await get_authenticated_user(request)
    return get_daily_summary(owner_id=owner_id)

@router.get("/api/inventory")
async def api_inventory(request: Request):
    owner_id = await get_authenticated_user(request)
    return {"products": get_all_products(owner_id)}

@router.get("/api/udhaar")
async def api_udhaar(request: Request):
    owner_id = await get_authenticated_user(request)
    return {"customers": get_overdue_customers(days=0, owner_id=owner_id)}

@router.get("/api/invoices")
async def api_invoices(request: Request):
    owner_id = await get_authenticated_user(request)
    return {"invoices": get_all_invoices(owner_id)}

@router.get("/api/weekly")
async def api_weekly(request: Request):
    owner_id = await get_authenticated_user(request)
    return get_weekly_summary(owner_id)

@router.get("/api/low-stock")
async def api_low_stock(request: Request):
    owner_id = await get_authenticated_user(request)
    return {"products": get_low_stock_products(owner_id)}

from pydantic import BaseModel as _BM

class AddProductBody(_BM):
    name: str
    selling_price: float
    stock: int = 0
    cost_price: float = 0
    gst_rate: float = 18.0
    warranty_months: int = 0

@router.post("/api/add-product")
async def api_add_product(request: Request, body: AddProductBody):
    owner_id = await get_authenticated_user(request)
    pid = create_product(
        name=body.name, selling_price=body.selling_price,
        stock=body.stock, cost_price=body.cost_price,
        gst_rate=body.gst_rate, warranty_months=body.warranty_months,
        owner_id=owner_id
    )
    return {"success": True, "product_id": pid}

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Mera Business Dashboard</title>
<style>
  :root{--saffron:#FF6600;--deep:#1a1a2e;--card:#ffffff;--bg:#f0f2f5;
        --green:#00b894;--red:#e17055;--blue:#0984e3;--gold:#fdcb6e;
        --text:#2d3436;--sub:#636e72;--border:#dfe6e9}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
       background:var(--bg);color:var(--text);min-height:100vh}
  header{background:linear-gradient(135deg,var(--deep) 0%,#16213e 100%);
         padding:16px 24px;display:flex;align-items:center;justify-content:space-between;
         box-shadow:0 2px 20px rgba(0,0,0,0.3);position:sticky;top:0;z-index:100}
  .logo{display:flex;align-items:center;gap:12px}
  .logo-icon{width:42px;height:42px;background:var(--saffron);border-radius:10px;
             display:flex;align-items:center;justify-content:center;font-size:22px}
  .logo-text h1{color:white;font-size:20px;font-weight:700}
  .logo-text p{color:#a0aec0;font-size:12px}
  .header-right{display:flex;align-items:center;gap:12px}
  .lang-btn{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);
            color:white;padding:6px 16px;border-radius:20px;cursor:pointer;font-size:13px;
            transition:all 0.2s}
  .lang-btn:hover{background:var(--saffron);border-color:var(--saffron)}
  .whatsapp-badge{background:#25D366;color:white;padding:6px 14px;border-radius:20px;
                  font-size:12px;font-weight:600;display:flex;align-items:center;gap:6px}
  nav{background:white;border-bottom:2px solid var(--border);padding:0 24px;
      display:flex;gap:4px;overflow-x:auto}
  .tab{padding:14px 20px;cursor:pointer;font-size:14px;font-weight:500;color:var(--sub);
       border-bottom:3px solid transparent;transition:all 0.2s;white-space:nowrap;
       display:flex;align-items:center;gap:8px}
  .tab.active{color:var(--saffron);border-color:var(--saffron)}
  .tab:hover{color:var(--saffron);background:#fff8f4}
  .page{display:none;padding:24px;max-width:1200px;margin:0 auto;animation:fadeIn 0.3s}
  .page.active{display:block}
  @keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px}
  .stat-card{background:white;border-radius:16px;padding:20px;
             box-shadow:0 2px 12px rgba(0,0,0,0.06);border-left:4px solid var(--saffron);
             display:flex;align-items:center;gap:16px}
  .stat-icon{width:48px;height:48px;border-radius:12px;display:flex;
             align-items:center;justify-content:center;font-size:22px;flex-shrink:0}
  .stat-info h3{font-size:13px;color:var(--sub);font-weight:500;margin-bottom:4px}
  .stat-info .value{font-size:24px;font-weight:700;color:var(--text)}
  .stat-info .sub{font-size:12px;color:var(--sub);margin-top:2px}
  .card{background:white;border-radius:16px;padding:20px;
        box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-bottom:20px}
  .card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
  .card-title{font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}
  table{width:100%;border-collapse:collapse}
  th{text-align:left;padding:10px 12px;font-size:12px;font-weight:600;
     color:var(--sub);border-bottom:2px solid var(--border);text-transform:uppercase;letter-spacing:0.5px}
  td{padding:12px;font-size:14px;border-bottom:1px solid var(--border);vertical-align:middle}
  tr:last-child td{border-bottom:none}
  tr:hover td{background:#fff8f4}
  .badge{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:500;display:inline-block}
  .badge-green{background:#d4edda;color:#155724}
  .badge-red{background:#f8d7da;color:#721c24}
  .badge-orange{background:#fff3cd;color:#856404}
  .badge-blue{background:#cce5ff;color:#004085}
  .btn{padding:8px 16px;border-radius:8px;border:none;cursor:pointer;
       font-size:13px;font-weight:500;transition:all 0.2s;display:inline-flex;
       align-items:center;gap:6px}
  .btn-primary{background:var(--saffron);color:white}
  .btn-primary:hover{background:#e55b00}
  .btn-green{background:var(--green);color:white}
  .btn-green:hover{opacity:0.9}
  .btn-sm{padding:5px 12px;font-size:12px}
  input,select{padding:8px 12px;border:1px solid var(--border);border-radius:8px;
               font-size:14px;width:100%;outline:none;transition:border 0.2s}
  input:focus,select:focus{border-color:var(--saffron)}
  .form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
  .form-group label{display:block;font-size:12px;font-weight:500;color:var(--sub);margin-bottom:6px}
  .empty{text-align:center;padding:40px;color:var(--sub)}
  .empty span{font-size:40px;display:block;margin-bottom:12px}
  .loading{text-align:center;padding:40px;color:var(--sub)}
  .progress-bar{height:6px;background:#e9ecef;border-radius:3px;overflow:hidden}
  .progress-fill{height:100%;background:var(--saffron);border-radius:3px;transition:width 0.3s}
  .chart-bar{display:flex;align-items:flex-end;gap:8px;height:160px;padding:16px 0}
  .bar-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
  .bar-fill{width:100%;background:linear-gradient(to top,var(--saffron),#ff9e40);
            border-radius:4px 4px 0 0;min-height:4px;transition:height 0.5s}
  .bar-label{font-size:10px;color:var(--sub);text-align:center}
  .bar-val{font-size:11px;font-weight:600;color:var(--saffron)}
  .alert-box{background:#fff8f4;border:1px solid #ffccaa;border-radius:10px;
             padding:14px;margin-bottom:16px;display:flex;gap:12px;align-items:flex-start}
  .refresh-btn{background:none;border:1px solid var(--border);color:var(--sub);
               border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px}
  .refresh-btn:hover{border-color:var(--saffron);color:var(--saffron)}
  @media(max-width:600px){
    .stats-grid{grid-template-columns:1fr 1fr}
    header{padding:12px 16px}
    .page{padding:16px}
    .tab{padding:12px 14px;font-size:13px}
    .logo-text h1{font-size:17px}
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">🏪</div>
    <div class="logo-text">
      <h1 id="h-brand">Mera Business</h1>
      <p id="h-sub">WhatsApp AI Business Agent</p>
    </div>
  </div>
  <div class="header-right">
    <div class="whatsapp-badge">📱 <span id="h-wp">WhatsApp Active</span></div>
    <button class="lang-btn" onclick="toggleLang()" id="lang-toggle">हिंदी</button>
  </div>
</header>

<nav>
  <div class="tab active" onclick="showTab('dashboard')" id="tab-dashboard">📊 <span>Dashboard</span></div>
  <div class="tab" onclick="showTab('inventory')"  id="tab-inventory">📦 <span>Inventory</span></div>
  <div class="tab" onclick="showTab('udhaar')"     id="tab-udhaar">💳 <span>Udhaar Bahi</span></div>
  <div class="tab" onclick="showTab('invoices')"   id="tab-invoices">🧾 <span>Invoices</span></div>
</nav>

<!-- DASHBOARD PAGE -->
<div class="page active" id="page-dashboard">
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card">
      <div class="stat-icon" style="background:#fff3e0">💰</div>
      <div class="stat-info">
        <h3 id="l-todaysales">Today's Sales</h3>
        <div class="value" id="stat-sales">₹0</div>
        <div class="sub" id="stat-sales-count">0 invoices</div>
      </div>
    </div>
    <div class="stat-card" style="border-color:var(--green)">
      <div class="stat-icon" style="background:#e8f8f5">💸</div>
      <div class="stat-info">
        <h3 id="l-payments">Payments Received</h3>
        <div class="value" id="stat-payments">₹0</div>
        <div class="sub" id="stat-pay-count">0 transactions</div>
      </div>
    </div>
    <div class="stat-card" style="border-color:var(--red)">
      <div class="stat-icon" style="background:#fdf2f2">⚠️</div>
      <div class="stat-info">
        <h3 id="l-udhaar">Outstanding Udhaar</h3>
        <div class="value" id="stat-udhaar">₹0</div>
        <div class="sub" id="l-allcust">All customers</div>
      </div>
    </div>
    <div class="stat-card" style="border-color:var(--blue)">
      <div class="stat-icon" style="background:#ebf5fb">📈</div>
      <div class="stat-info">
        <h3 id="l-netcash">Net Cash Flow</h3>
        <div class="value" id="stat-net">₹0</div>
        <div class="sub" id="l-today">Today</div>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px" class="chart-grid">
    <div class="card">
      <div class="card-header">
        <div class="card-title">📊 <span id="l-weekly">Weekly Sales</span></div>
        <button class="refresh-btn" onclick="loadDashboard()">↻</button>
      </div>
      <div class="chart-bar" id="weekly-chart">
        <div class="loading">Loading...</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">⚠️ <span id="l-lowstock">Low Stock Alert</span></div>
      </div>
      <div id="low-stock-list"><div class="loading">Loading...</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title">💳 <span id="l-overduedue">Overdue Udhaar</span></div>
    </div>
    <div id="overdue-list"><div class="loading">Loading...</div></div>
  </div>
</div>

<!-- INVENTORY PAGE -->
<div class="page" id="page-inventory">
  <div class="card" style="margin-bottom:20px">
    <div class="card-header">
      <div class="card-title">➕ <span id="l-addprod">Add New Product</span></div>
    </div>
    <div class="form-grid" id="add-product-form">
      <div class="form-group">
        <label id="l-prodname">Product Name</label>
        <input type="text" id="inp-name" placeholder="Vivo V29">
      </div>
      <div class="form-group">
        <label id="l-price">Selling Price (₹)</label>
        <input type="number" id="inp-price" placeholder="29999">
      </div>
      <div class="form-group">
        <label id="l-stock">Stock Quantity</label>
        <input type="number" id="inp-stock" placeholder="50">
      </div>
      <div class="form-group">
        <label id="l-costprice">Cost Price (₹)</label>
        <input type="number" id="inp-cost" placeholder="25000">
      </div>
      <div class="form-group">
        <label id="l-gst">GST Rate (%)</label>
        <select id="inp-gst">
          <option value="18" selected>18% (Electronics)</option>
          <option value="5">5% (Essentials)</option>
          <option value="12">12% (Standard)</option>
          <option value="28">28% (Luxury)</option>
        </select>
      </div>
      <div class="form-group" style="display:flex;align-items:flex-end">
        <button class="btn btn-primary" style="width:100%" onclick="addProduct()" id="btn-addprod">
          ➕ Add Product
        </button>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title">📦 <span id="l-invtable">Inventory</span></div>
      <button class="refresh-btn" onclick="loadInventory()">↻</button>
    </div>
    <div id="inventory-table"><div class="loading">Loading...</div></div>
  </div>
</div>

<!-- UDHAAR BAHI PAGE -->
<div class="page" id="page-udhaar">
  <div class="card">
    <div class="card-header">
      <div class="card-title">💳 <span id="l-udhaarbook">Udhaar Bahi (Credit Ledger)</span></div>
      <button class="refresh-btn" onclick="loadUdhaar()">↻</button>
    </div>
    <div id="udhaar-table"><div class="loading">Loading...</div></div>
  </div>
</div>

<!-- INVOICES PAGE -->
<div class="page" id="page-invoices">
  <div class="card">
    <div class="card-header">
      <div class="card-title">🧾 <span id="l-invlist">Invoice List</span></div>
      <button class="refresh-btn" onclick="loadInvoices()">↻</button>
    </div>
    <div id="invoices-table"><div class="loading">Loading...</div></div>
  </div>
</div>

<script>
const T = {
  en: {
    brand:"Mera Business",sub:"WhatsApp AI Business Agent",wp:"WhatsApp Active",
    todaysales:"Today's Sales",payments:"Payments Received",udhaar:"Outstanding Udhaar",
    netcash:"Net Cash Flow",allcust:"All customers",today:"Today",
    weekly:"Weekly Sales (7 Days)",lowstock:"Low Stock Alert",overduedue:"Overdue Udhaar",
    addprod:"Add New Product",prodname:"Product Name",price:"Selling Price (₹)",
    stock:"Stock Quantity",costprice:"Cost Price (₹)",gst:"GST Rate (%)",
    btnaddprod:"➕ Add Product",invtable:"Inventory",
    udhaarbook:"Udhaar Bahi (Credit Ledger)",invlist:"Invoice List",
    tabdash:"Dashboard",tabinv:"Inventory",tabudh:"Udhaar Bahi",tabinvl:"Invoices",
    invoices:"invoices",transactions:"transactions",
    name:"Name",phone:"Phone",balance:"Balance (₹)",days:"Days",action:"Action",
    prodname2:"Product",price2:"Price",stockqty:"Stock",gstrate:"GST",margin:"Margin",
    invno:"Invoice #",customer:"Customer",amount:"Amount",status:"Status",date:"Date",mode:"Mode",
    paid:"Paid",pending:"Pending",partial:"Partial Credit",
    nooverdue:"No overdue customers! 🎉",nolowstock:"All stock levels healthy 👍",
    noproducts:"No products added yet",nocustomers:"No udhaar pending 🎉",noinvoices:"No invoices yet",
    addstock:"+ Stock",
  },
  hi: {
    brand:"मेरा बिज़नेस",sub:"WhatsApp AI बिज़नेस असिस्टेंट",wp:"WhatsApp चालू है",
    todaysales:"आज की बिक्री",payments:"प्राप्त भुगतान",udhaar:"बकाया उधार",
    netcash:"नेट कैश फ्लो",allcust:"सभी ग्राहक",today:"आज",
    weekly:"साप्ताहिक बिक्री (7 दिन)",lowstock:"कम स्टॉक अलर्ट",overduedue:"बकाया उधार",
    addprod:"नया प्रोडक्ट जोड़ें",prodname:"प्रोडक्ट का नाम",price:"बिक्री मूल्य (₹)",
    stock:"स्टॉक मात्रा",costprice:"लागत मूल्य (₹)",gst:"GST दर (%)",
    btnaddprod:"➕ प्रोडक्ट जोड़ें",invtable:"माल सूची",
    udhaarbook:"उधार बही (क्रेडिट लेजर)",invlist:"बिल सूची",
    tabdash:"डैशबोर्ड",tabinv:"माल सूची",tabudh:"उधार बही",tabinvl:"बिल",
    invoices:"बिल",transactions:"लेनदेन",
    name:"नाम",phone:"फ़ोन",balance:"बकाया (₹)",days:"दिन",action:"काम",
    prodname2:"प्रोडक्ट",price2:"मूल्य",stockqty:"स्टॉक",gstrate:"GST",margin:"मार्जिन",
    invno:"बिल नं.",customer:"ग्राहक",amount:"रकम",status:"स्थिति",date:"तारीख",mode:"मोड",
    paid:"चुकाया",pending:"बाकी",partial:"आंशिक",
    nooverdue:"कोई बकाया नहीं! 🎉",nolowstock:"सारा स्टॉक ठीक है 👍",
    noproducts:"कोई प्रोडक्ट नहीं है",nocustomers:"कोई उधार नहीं 🎉",noinvoices:"कोई बिल नहीं",
    addstock:"+ स्टॉक",
  }
};
let lang = 'en';
function t(k){return T[lang][k]||T.en[k]||k}

function toggleLang(){
  lang = lang==='en'?'hi':'en';
  document.getElementById('lang-toggle').textContent = lang==='en'?'हिंदी':'English';
  applyLang();
}

function applyLang(){
  const ids = ['brand','sub','wp','todaysales','payments','udhaar','netcash',
    'allcust','today','weekly','lowstock','overduedue','addprod','prodname','price',
    'stock','costprice','gst','btnaddprod','invtable','udhaarbook','invlist'];
  const map = {
    'brand':'h-brand','sub':'h-sub','wp':'h-wp','todaysales':'l-todaysales',
    'payments':'l-payments','udhaar':'l-udhaar','netcash':'l-netcash',
    'allcust':'l-allcust','today':'l-today','weekly':'l-weekly','lowstock':'l-lowstock',
    'overduedue':'l-overduedue','addprod':'l-addprod','prodname':'l-prodname',
    'price':'l-price','stock':'l-stock','costprice':'l-costprice','gst':'l-gst',
    'btnaddprod':'btn-addprod','invtable':'l-invtable','udhaarbook':'l-udhaarbook',
    'invlist':'l-invlist'
  };
  for(const[k,id] of Object.entries(map)){
    const el=document.getElementById(id);
    if(el)el.textContent=t(k);
  }
  document.getElementById('tab-dashboard').querySelector('span').textContent=t('tabdash');
  document.getElementById('tab-inventory').querySelector('span').textContent=t('tabinv');
  document.getElementById('tab-udhaar').querySelector('span').textContent=t('tabudh');
  document.getElementById('tab-invoices').querySelector('span').textContent=t('tabinvl');
  // Re-render active table
  const active=document.querySelector('.page.active').id.replace('page-','');
  if(active==='dashboard')loadDashboard();
  else if(active==='inventory')loadInventory();
  else if(active==='udhaar')loadUdhaar();
  else if(active==='invoices')loadInvoices();
}

function fmt(n){return'₹'+(+n||0).toLocaleString('en-IN',{maximumFractionDigits:0})}

function showTab(name){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.getElementById('page-'+name).classList.add('active');
  if(name==='dashboard')loadDashboard();
  else if(name==='inventory')loadInventory();
  else if(name==='udhaar')loadUdhaar();
  else if(name==='invoices')loadInvoices();
}

async function loadDashboard(){
  try{
    const[s,w,ls,od]=await Promise.all([
      fetch('/api/summary').then(r=>r.json()),
      fetch('/api/weekly').then(r=>r.json()),
      fetch('/api/low-stock').then(r=>r.json()),
      fetch('/api/udhaar').then(r=>r.json()),
    ]);
    document.getElementById('stat-sales').textContent=fmt(s.sales?.total||0);
    document.getElementById('stat-sales-count').textContent=`${s.sales?.count||0} ${t('invoices')}`;
    document.getElementById('stat-payments').textContent=fmt(s.payments?.total||0);
    document.getElementById('stat-pay-count').textContent=`${s.payments?.count||0} ${t('transactions')}`;
    document.getElementById('stat-udhaar').textContent=fmt(s.outstanding_udhaar||0);
    const net=s.net_cash_flow||0;
    const netEl=document.getElementById('stat-net');
    netEl.textContent=fmt(Math.abs(net));
    netEl.style.color=net>=0?'var(--green)':'var(--red)';

    // Weekly chart
    const weekly=w.weekly_sales||[];
    const maxVal=Math.max(...weekly.map(d=>d.revenue),1);
    const chartEl=document.getElementById('weekly-chart');
    if(weekly.length===0){chartEl.innerHTML=`<div class="empty">No data</div>`;}
    else { chartEl.innerHTML=weekly.map(d=>{
      const h=Math.max(8,(d.revenue/maxVal)*130);
      const day=d.day?new Date(d.day+'T00:00:00').toLocaleDateString('en-IN',{weekday:'short'}):d.day;
      return`<div class="bar-col">
        <div class="bar-val">${fmt(d.revenue).replace('₹','')}</div>
        <div class="bar-fill" style="height:${h}px"></div>
        <div class="bar-label">${day}</div>
      </div>`;
    }).join(''); }

    // Low stock
    const lsEl=document.getElementById('low-stock-list');
    const prods=ls.products||[];
    if(!prods.length){lsEl.innerHTML=`<div class="empty">${t('nolowstock')}</div>`;return;}
    lsEl.innerHTML=`<table><tr><th>${t('prodname2')}</th><th>${t('stockqty')}</th><th>Alert</th></tr>`+
      prods.map(p=>{
        const pct=Math.min(100,(p.stock/Math.max(p.low_stock_alert,1))*100);
        return`<tr><td>${p.name}</td><td>
          <div class="progress-bar" style="width:120px"><div class="progress-fill" style="width:${pct}%;background:${pct<30?'var(--red)':'var(--gold)'}"></div></div>
          <span style="font-size:12px;color:${pct<30?'var(--red)':'var(--sub)'}">${p.stock} units</span>
        </td><td><span class="badge badge-orange">${p.low_stock_alert}</span></td></tr>`;
      }).join('')+'</table>';

    // Overdue
    const odEl=document.getElementById('overdue-list');
    const custs=(od.customers||[]).filter(c=>c.outstanding_balance>0);
    if(!custs.length){odEl.innerHTML=`<div class="empty">${t('nooverdue')}</div>`;return;}
    odEl.innerHTML=`<table><tr><th>${t('name')}</th><th>${t('phone')}</th><th>${t('balance')}</th><th>${t('days')}</th></tr>`+
      custs.map(c=>`<tr>
        <td><strong>${c.name}</strong></td>
        <td>${c.phone||'-'}</td>
        <td style="color:var(--red);font-weight:700">${fmt(c.outstanding_balance)}</td>
        <td><span class="badge ${(c.days_overdue||0)>30?'badge-red':'badge-orange'}">${c.days_overdue||0}d</span></td>
      </tr>`).join('')+'</table>';
  }catch(e){console.error(e)}
}

async function loadInventory(){
  const el=document.getElementById('inventory-table');
  try{
    const d=await fetch('/api/inventory').then(r=>r.json());
    const prods=d.products||[];
    if(!prods.length){el.innerHTML=`<div class="empty"><span>📦</span>${t('noproducts')}</div>`;return;}
    el.innerHTML=`<table>
      <tr><th>${t('prodname2')}</th><th>${t('price2')}</th><th>${t('costprice')}</th>
          <th>${t('stockqty')}</th><th>${t('gstrate')}</th><th>${t('margin')}</th></tr>`+
    prods.map(p=>{
      const margin=p.selling_price>0?((p.selling_price-p.cost_price)/p.selling_price*100).toFixed(1):0;
      return`<tr>
        <td><strong>${p.name}</strong><br><span style="font-size:11px;color:var(--sub)">${p.sku||''}</span></td>
        <td>${fmt(p.selling_price)}</td>
        <td>${fmt(p.cost_price)}</td>
        <td><span class="badge ${p.stock<=p.low_stock_alert?'badge-red':'badge-green'}">${p.stock} units</span></td>
        <td><span class="badge badge-blue">${p.gst_rate}%</span></td>
        <td><span style="color:var(--green);font-weight:600">${margin}%</span></td>
      </tr>`;
    }).join('')+'</table>';
  }catch(e){el.innerHTML='<div class="empty">Error loading inventory</div>';}
}

async function loadUdhaar(){
  const el=document.getElementById('udhaar-table');
  try{
    const d=await fetch('/api/udhaar').then(r=>r.json());
    const custs=(d.customers||[]);
    if(!custs.length){el.innerHTML=`<div class="empty"><span>🎉</span>${t('nocustomers')}</div>`;return;}
    el.innerHTML=`<table>
      <tr><th>${t('name')}</th><th>${t('phone')}</th><th>${t('balance')}</th><th>${t('days')}</th></tr>`+
    custs.map(c=>`<tr>
      <td><strong>${c.name}</strong></td>
      <td>${c.phone||'-'}</td>
      <td style="color:${c.outstanding_balance>0?'var(--red)':'var(--green)'};font-weight:700">${fmt(c.outstanding_balance)}</td>
      <td>${c.days_overdue!=null?`<span class="badge ${(c.days_overdue||0)>30?'badge-red':'badge-orange'}">${c.days_overdue||0} days</span>`:'—'}</td>
    </tr>`).join('')+'</table>';
  }catch(e){el.innerHTML='<div class="empty">Error loading udhaar</div>';}
}

async function loadInvoices(){
  const el=document.getElementById('invoices-table');
  try{
    const d=await fetch('/api/invoices').then(r=>r.json());
    const invs=d.invoices||[];
    if(!invs.length){el.innerHTML=`<div class="empty"><span>🧾</span>${t('noinvoices')}</div>`;return;}
    const statusLabel={paid:t('paid'),pending:t('pending'),partial:t('partial')};
    const statusClass={paid:'badge-green',pending:'badge-red',partial:'badge-orange'};
    el.innerHTML=`<table>
      <tr><th>${t('invno')}</th><th>${t('customer')}</th><th>${t('amount')}</th>
          <th>${t('status')}</th><th>${t('mode')}</th><th>${t('date')}</th></tr>`+
    invs.map(i=>{
      const d2=i.invoice_date?new Date(i.invoice_date).toLocaleDateString('en-IN'):'—';
      return`<tr>
        <td><strong>${i.invoice_number}</strong><br><span style="font-size:11px;color:var(--sub)">${i.items_summary||''}</span></td>
        <td>${i.customer_name}</td>
        <td><strong>${fmt(i.total_amount)}</strong></td>
        <td><span class="badge ${statusClass[i.status]||'badge-blue'}">${statusLabel[i.status]||i.status}</span></td>
        <td>${i.payment_mode||'Udhaar'}</td>
        <td style="font-size:12px">${d2}</td>
      </tr>`;
    }).join('')+'</table>';
  }catch(e){el.innerHTML='<div class="empty">Error loading invoices</div>';}
}

async function addProduct(){
  const name=document.getElementById('inp-name').value.trim();
  const price=+document.getElementById('inp-price').value;
  const stock=+document.getElementById('inp-stock').value;
  const cost=+document.getElementById('inp-cost').value;
  const gst=+document.getElementById('inp-gst').value;
  if(!name||!price){alert(lang==='hi'?'नाम और मूल्य ज़रूरी है':'Name and price required');return;}
  try{
    const r=await fetch('/api/add-product',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,selling_price:price,stock,cost_price:cost,gst_rate:gst})
    });
    if(r.ok){
      document.getElementById('inp-name').value='';
      document.getElementById('inp-price').value='';
      document.getElementById('inp-stock').value='';
      document.getElementById('inp-cost').value='';
      alert(lang==='hi'?`✅ ${name} जोड़ा गया!`:`✅ ${name} added!`);
      loadInventory();
    }
  }catch(e){alert('Error: '+e)}
}

// Load on start
loadDashboard();

// Auto-refresh every 30 seconds
setInterval(()=>{
  const active=document.querySelector('.page.active').id.replace('page-','');
  if(active==='dashboard')loadDashboard();
  else if(active==='inventory')loadInventory();
  else if(active==='udhaar')loadUdhaar();
  else if(active==='invoices')loadInvoices();
},30000);
</script>
</body>
</html>
"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Mera Business</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        .login-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo-icon {
            font-size: 60px;
            margin-bottom: 10px;
        }
        h1 {
            color: #1a237e;
            font-size: 28px;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            text-align: center;
            font-size: 14px;
            margin-bottom: 30px;
        }
        .step {
            display: none;
        }
        .step.active {
            display: block;
        }
        label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-bottom: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        button.secondary {
            background: #f5f5f5;
            color: #666;
        }
        button.secondary:hover {
            background: #e0e0e0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .note {
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 20px;
            line-height: 1.5;
        }
        .error {
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        .success {
            background: #efe;
            border: 1px solid #cfc;
            color: #3c3;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .whatsapp-note {
            background: #e8f5e9;
            border: 1px solid #4caf50;
            color: #2e7d32;
            padding: 12px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 13px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">🏪</div>
            <h1>Mera Business</h1>
            <p class="subtitle">AI Business Assistant</p>
        </div>
        
        <div class="error" id="error"></div>
        <div class="success" id="success"></div>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #666;">Processing...</p>
        </div>
        
        <!-- Step 1: Phone Number -->
        <div class="step active" id="step1">
            <label for="phone">Phone Number</label>
            <input type="tel" id="phone" placeholder="+919876543210" maxlength="13" />
            <button onclick="sendOTP()">Send OTP</button>
            
            <div class="whatsapp-note">
                <strong>📱 New user?</strong><br>
                Register via WhatsApp first by sending any message to our bot.
            </div>
        </div>
        
        <!-- Step 2: OTP Verification -->
        <div class="step" id="step2">
            <label for="otp">Enter OTP</label>
            <input type="text" id="otp" placeholder="000000" maxlength="6" inputmode="numeric" />
            <button onclick="verifyOTP()">Verify & Login</button>
            <button class="secondary" onclick="resendOTP()">Resend OTP</button>
            
            <p class="note">
                OTP sent to your WhatsApp<br>
                Valid for 5 minutes
            </p>
        </div>
    </div>
    
    <script>
        let currentPhone = '';
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
        
        function showSuccess(message) {
            const successDiv = document.getElementById('success');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
        }
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        
        function sendOTP() {
            const phone = document.getElementById('phone').value.trim();
            
            // Validate phone
            if (!phone.startsWith('+91') || phone.length !== 13) {
                showError('Please enter a valid Indian phone number with +91');
                return;
            }
            
            currentPhone = phone;
            showLoading(true);
            
            fetch('/api/send-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone})
            })
            .then(r => r.json())
            .then(data => {
                showLoading(false);
                if (data.success) {
                    document.getElementById('step1').classList.remove('active');
                    document.getElementById('step2').classList.add('active');
                    showSuccess('OTP sent to your WhatsApp!');
                } else {
                    showError(data.error || 'Failed to send OTP');
                }
            })
            .catch(err => {
                showLoading(false);
                showError('Network error. Please try again.');
            });
        }
        
        function verifyOTP() {
            const otp = document.getElementById('otp').value.trim();
            
            if (otp.length !== 6) {
                showError('Please enter 6-digit OTP');
                return;
            }
            
            showLoading(true);
            
            fetch('/api/verify-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: currentPhone, otp: otp})
            })
            .then(r => r.json())
            .then(data => {
                showLoading(false);
                if (data.success) {
                    showSuccess('Login successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = data.redirect || '/';
                    }, 1000);
                } else {
                    showError(data.error || 'Invalid OTP');
                }
            })
            .catch(err => {
                showLoading(false);
                showError('Verification failed. Please try again.');
            });
        }
        
        function resendOTP() {
            sendOTP();
        }
        
        // Enter key handling
        document.getElementById('phone').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendOTP();
        });
        
        document.getElementById('otp').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') verifyOTP();
        });
    </script>
</body>
</html>
"""
