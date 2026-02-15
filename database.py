"""
Mera Business — Database Layer
SQLite schema + all business logic functions
Multi-tenant ready: every function accepts optional owner_id
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging, threading
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)
_write_lock = threading.RLock()  # Reentrant lock allows nested calls (e.g. create_invoice → create_customer)
DATABASE_PATH = "bharat_biz.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")   # wait up to 10s instead of failing instantly
    conn.execute("PRAGMA synchronous=NORMAL;")    # faster writes, still safe with WAL
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize all tables + run migrations for owner_id multi-tenancy."""
    conn = get_db_connection()
    c = conn.cursor()

    # ── Business Owners ───────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS business_owners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        business_name TEXT NOT NULL,
        business_address TEXT,
        business_gstin TEXT,
        business_upi_id TEXT,
        onboarding_complete INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_active TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Products ──────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        name TEXT NOT NULL,
        sku TEXT,
        stock INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'piece',
        cost_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        gst_rate REAL DEFAULT 18.0,
        warranty_months INTEGER DEFAULT 0,
        low_stock_alert INTEGER DEFAULT 10,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Customers ─────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        gstin TEXT,
        outstanding_balance REAL DEFAULT 0,
        credit_limit REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Invoices ──────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        invoice_number TEXT NOT NULL,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        invoice_date TEXT DEFAULT CURRENT_TIMESTAMP,
        due_date TEXT,
        subtotal REAL DEFAULT 0,
        gst_amount REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        payment_mode TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )""")

    # ── Invoice Items ─────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT DEFAULT 'piece',
        rate REAL NOT NULL,
        gst_rate REAL DEFAULT 18.0,
        amount REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id)
    )""")

    # ── Payments ──────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        invoice_id INTEGER,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
        payment_mode TEXT DEFAULT 'UPI',
        utr_number TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )""")

    # ── Expenses ──────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT DEFAULT CURRENT_TIMESTAMP,
        payment_mode TEXT,
        vendor TEXT,
        gst_amount REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Udhaar Ledger ─────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS udhaar_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        balance REAL NOT NULL,
        description TEXT,
        transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
        reminder_sent INTEGER DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )""")

    # ── GST Filings ───────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS gst_filings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        filing_period TEXT NOT NULL,
        gstr_type TEXT NOT NULL,
        total_sales REAL DEFAULT 0,
        total_purchases REAL DEFAULT 0,
        gst_collected REAL DEFAULT 0,
        gst_paid REAL DEFAULT 0,
        net_gst REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        filed_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Activity Log ──────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        action_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        details TEXT,
        user_phone TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Warranty Tracking ─────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS warranty_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL DEFAULT 'default',
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        invoice_id INTEGER,
        purchase_date TEXT DEFAULT CURRENT_TIMESTAMP,
        warranty_months INTEGER NOT NULL,
        warranty_expiry_date TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (invoice_id) REFERENCES invoices (id)
    )""")

    conn.commit()

    # ── Migrations: add owner_id to existing tables if column missing ─────────
    migrations = [
        ("products",      "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("products",      "warranty_months INTEGER DEFAULT 0"),
        ("customers",     "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("invoices",      "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("payments",      "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("expenses",      "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("udhaar_ledger", "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("gst_filings",   "owner_id TEXT NOT NULL DEFAULT 'default'"),
        ("activity_log",  "owner_id TEXT NOT NULL DEFAULT 'default'"),
    ]
    for table, col_def in migrations:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            conn.commit()
            logger.info(f"Migration: added owner_id to {table}")
        except Exception:
            pass  # Column already exists — that's fine

    conn.close()
    logger.info("Database initialized / migrated successfully")

# ==================== Business Owner Functions ====================

def create_business_owner(phone: str, name: str, business_name: str, **kwargs) -> dict:
    """Create new business owner account"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Check if already exists
        c.execute("SELECT * FROM business_owners WHERE phone = ?", (phone,))
        existing = c.fetchone()
        if existing:
            raise ValueError("User already registered")
        
        c.execute("""
            INSERT INTO business_owners 
            (phone, name, business_name, business_address, business_gstin, business_upi_id, onboarding_complete)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (phone, name, business_name, 
              kwargs.get('business_address'), 
              kwargs.get('business_gstin'),
              kwargs.get('business_upi_id')))
        
        owner_id = c.lastrowid
        conn.commit()
        
        c.execute("SELECT * FROM business_owners WHERE id = ?", (owner_id,))
        owner = dict(c.fetchone())
        
        logger.info(f"Created business owner: {name} ({phone})")
        return owner
    finally:
        conn.close()


def get_owner_onboarding_status(phone: str) -> dict:
    """Check if user has completed onboarding"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        c.execute("SELECT * FROM business_owners WHERE phone = ?", (phone,))
        owner = c.fetchone()
        
        if not owner:
            return {"exists": False, "onboarding_complete": False}
        
        return {
            "exists": True,
            "onboarding_complete": bool(owner['onboarding_complete']),
            "name": owner.get('name'),
            "business_name": owner.get('business_name'),
            "business_address": owner.get('business_address'),
            "business_gstin": owner.get('business_gstin')
        }
    finally:
        conn.close()


def get_business_owner(phone: str) -> Optional[dict]:
    """Get business owner details by phone"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM business_owners WHERE phone = ?", (phone,))
        owner = c.fetchone()
        return dict(owner) if owner else None
    finally:
        conn.close()


def update_business_owner(phone: str, **kwargs) -> bool:
    """Update business owner details"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        updates = []
        values = []
        
        for key in ['name', 'business_name', 'business_address', 'business_gstin', 'business_upi_id']:
            if key in kwargs:
                updates.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if not updates:
            return False
        
        values.append(phone)
        query = f"UPDATE business_owners SET {', '.join(updates)} WHERE phone = ?"
        
        c.execute(query, values)
        conn.commit()
        
        return c.rowcount > 0
    finally:
        conn.close()

# ==================== Product Functions ====================

def create_product(name: str, sku: Optional[str] = None, stock: int = 0,
                   cost_price: float = 0, selling_price: float = 0,
                   gst_rate: float = 18.0, owner_id: str = 'default', **kwargs) -> int:
    with _write_lock:
        conn = get_db_connection()
        try:
            c = conn.cursor()
            # Check if product with this name already exists for this owner
            c.execute("SELECT id FROM products WHERE name=? AND owner_id=?", (name, owner_id))
            existing = c.fetchone()
            if existing:
                return existing['id']
            c.execute("""
                INSERT INTO products (owner_id, name, sku, stock, cost_price, selling_price,
                                      gst_rate, unit, low_stock_alert, warranty_months)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (owner_id, name, sku or f"SKU{int(datetime.now().timestamp())}",
                  stock, cost_price, selling_price, gst_rate,
                  kwargs.get('unit', 'piece'), kwargs.get('low_stock_alert', 10),
                  kwargs.get('warranty_months', 0)))
            pid = c.lastrowid
            conn.commit()
            logger.info(f"Created product: {name} (owner={owner_id})")
            return pid
        finally:
            conn.close()


def update_inventory(product_name: str, quantity: int,
                     operation: str = "reduce", owner_id: str = 'default') -> Dict[str, Any]:
    with _write_lock:
        conn = get_db_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE name LIKE ? AND owner_id=? ORDER BY id LIMIT 1",
                      (f"%{product_name}%", owner_id))
            product = c.fetchone()
            if not product:
                c.execute("SELECT * FROM products WHERE name LIKE ? ORDER BY id LIMIT 1",
                          (f"%{product_name}%",))
                product = c.fetchone()
            if not product:
                raise ValueError(f"Product '{product_name}' not found")
            new_stock = (product['stock'] + quantity) if operation == "add" else max(0, product['stock'] - quantity)
            c.execute("UPDATE products SET stock=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (new_stock, product['id']))
            conn.commit()
            c.execute("SELECT * FROM products WHERE id=?", (product['id'],))
            updated = dict(c.fetchone())
            return updated
        finally:
            conn.close()


def get_low_stock_products(owner_id: str = 'default') -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM products
        WHERE stock <= low_stock_alert AND owner_id=?
        ORDER BY stock ASC
    """, (owner_id,))
    products = [dict(r) for r in c.fetchall()]
    conn.close()
    return products


def get_all_products(owner_id: str = 'default') -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE owner_id=? ORDER BY name", (owner_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ==================== Customer Functions ====================

def create_customer(name: str, phone: str = '', owner_id: str = 'default', **kwargs) -> int:
    with _write_lock:
        conn = get_db_connection()
        try:
            c = conn.cursor()
            if phone:
                c.execute("SELECT id FROM customers WHERE phone=? AND owner_id=?", (phone, owner_id))
            else:
                c.execute("SELECT id FROM customers WHERE name=? AND owner_id=?", (name, owner_id))
            existing = c.fetchone()
            if existing:
                cid = existing['id']
                c.execute("""UPDATE customers SET name=?, email=?, address=?, gstin=?,
                             updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                          (name, kwargs.get('email'), kwargs.get('address'), kwargs.get('gstin'), cid))
            else:
                c.execute("""INSERT INTO customers (owner_id, name, phone, email, address, gstin, credit_limit)
                             VALUES (?,?,?,?,?,?,?)""",
                          (owner_id, name, phone or f"+91{int(datetime.now().timestamp())%10000000000}",
                           kwargs.get('email'), kwargs.get('address'), kwargs.get('gstin'),
                           kwargs.get('credit_limit', 0)))
                cid = c.lastrowid
            conn.commit()
            return cid
        finally:
            conn.close()


def get_customer_by_name(name: str, owner_id: str = 'default') -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE name LIKE ? AND owner_id=? ORDER BY created_at DESC LIMIT 1",
              (f"%{name}%", owner_id))
    row = c.fetchone()
    if not row:
        # Fallback: any owner (backward compat with old data)
        c.execute("SELECT * FROM customers WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1",
                  (f"%{name}%",))
        row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_customers(owner_id: str = 'default') -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE owner_id=? ORDER BY outstanding_balance DESC", (owner_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ==================== Invoice Functions ====================

def create_invoice(customer_name: str, items: List[Dict[str, Any]],
                   payment_mode: Optional[str] = None, notes: Optional[str] = None,
                   owner_id: str = 'default') -> Dict[str, Any]:
    with _write_lock:
        conn = get_db_connection()
        try:
            c = conn.cursor()
            
            # Get customer using existing cursor (don't call get_customer_by_name - it opens a new connection!)
            c.execute("SELECT * FROM customers WHERE name LIKE ? AND owner_id=? ORDER BY created_at DESC LIMIT 1",
                      (f"%{customer_name}%", owner_id))
            customer = c.fetchone()
            if not customer:
                # Fallback: any owner (backward compat)
                c.execute("SELECT * FROM customers WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1",
                          (f"%{customer_name}%",))
                customer = c.fetchone()
            
            if not customer:
                cid = create_customer(customer_name, owner_id=owner_id)
                c.execute("SELECT * FROM customers WHERE id=?", (cid,))
                customer = c.fetchone()
            
            customer = dict(customer)
            cid = customer['id']

            invoice_number = f"INV{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp())%10000:04d}"

            subtotal = sum(i['quantity'] * i['rate'] for i in items)
            gst_amount = sum(i['quantity'] * i['rate'] * (i.get('gst_rate', 18) / 100) for i in items)
            total_amount = subtotal + gst_amount

            status = 'paid' if payment_mode and payment_mode.lower() != 'udhaar' else 'pending'
            actual_mode = None if (not payment_mode or payment_mode.lower() == 'udhaar') else payment_mode

            c.execute("""INSERT INTO invoices
                         (owner_id, invoice_number, customer_id, customer_name, subtotal,
                          gst_amount, total_amount, payment_mode, notes, status)
                         VALUES (?,?,?,?,?,?,?,?,?,?)""",
                      (owner_id, invoice_number, cid, customer['name'], subtotal,
                       gst_amount, total_amount, actual_mode, notes, status))
            inv_id = c.lastrowid

            for item in items:
                c.execute("""INSERT INTO invoice_items
                             (invoice_id, product_name, quantity, rate, gst_rate, amount)
                             VALUES (?,?,?,?,?,?)""",
                          (inv_id, item['product_name'], item['quantity'], item['rate'],
                           item.get('gst_rate', 18), item['quantity'] * item['rate']))
                try:
                    # Update inventory
                    product = update_inventory(item['product_name'], int(item['quantity']), "reduce", owner_id)
                    
                    # Track warranty if product has warranty
                    if product and product.get('warranty_months', 0) > 0:
                        from dateutil.relativedelta import relativedelta
                        purchase_date = datetime.now()
                        warranty_months = product['warranty_months']
                        expiry_date = purchase_date + relativedelta(months=warranty_months)
                        
                        c.execute("""
                            INSERT INTO warranty_tracking 
                            (owner_id, product_id, product_name, customer_id, customer_name, 
                             invoice_id, purchase_date, warranty_months, warranty_expiry_date)
                            VALUES (?,?,?,?,?,?,?,?,?)
                        """, (owner_id, product['id'], product['name'], cid, customer['name'],
                              inv_id, purchase_date.strftime('%Y-%m-%d'), warranty_months, 
                              expiry_date.strftime('%Y-%m-%d')))
                        
                        logger.info(f"Warranty tracked: {product['name']} for {customer['name']}")
                except ValueError:
                    logger.warning(f"Product not in inventory: {item['product_name']}")

            if not actual_mode:  # Udhaar
                c.execute("""INSERT INTO udhaar_ledger
                             (owner_id, customer_id, customer_name, transaction_type, amount, balance, description)
                             VALUES (?,?,?,'debit',?,?,?)""",
                          (owner_id, cid, customer['name'], total_amount, total_amount,
                           f"Invoice {invoice_number}"))
                c.execute("UPDATE customers SET outstanding_balance=outstanding_balance+? WHERE id=?",
                          (total_amount, cid))

            # Log activity
            c.execute("""INSERT INTO activity_log (owner_id, action_type, entity_type, entity_id, details)
                         VALUES (?,?,?,?,?)""",
                      (owner_id, 'CREATE_INVOICE', 'invoice', inv_id,
                       f"{invoice_number} | {customer_name} | ₹{total_amount:.2f}"))

            conn.commit()
            c.execute("""SELECT i.*, GROUP_CONCAT(ii.product_name||' x'||ii.quantity) as items_summary
                         FROM invoices i LEFT JOIN invoice_items ii ON i.id=ii.invoice_id
                         WHERE i.id=? GROUP BY i.id""", (inv_id,))
            invoice = dict(c.fetchone())
            logger.info(f"Invoice created: {invoice_number}")
            return invoice
        finally:
            conn.close()


def get_all_invoices(owner_id: str = 'default', limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT i.*, GROUP_CONCAT(ii.product_name||' x'||ii.quantity) as items_summary
                 FROM invoices i LEFT JOIN invoice_items ii ON i.id=ii.invoice_id
                 WHERE i.owner_id=? GROUP BY i.id ORDER BY i.created_at DESC LIMIT ?""",
              (owner_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_invoice_items(invoice_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ==================== Payment Functions ====================

def record_payment(customer_name: str, amount: float, payment_mode: str = "UPI",
                   utr_number: Optional[str] = None, invoice_number: Optional[str] = None,
                   owner_id: str = 'default') -> Dict[str, Any]:
    with _write_lock:
        conn = get_db_connection()
        try:
            c = conn.cursor()

            # Get customer using existing cursor (don't call get_customer_by_name - it opens a new connection!)
            c.execute("SELECT * FROM customers WHERE name LIKE ? AND owner_id=? ORDER BY created_at DESC LIMIT 1",
                      (f"%{customer_name}%", owner_id))
            customer = c.fetchone()
            if not customer:
                # Fallback: any owner (backward compat)
                c.execute("SELECT * FROM customers WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1",
                          (f"%{customer_name}%",))
                customer = c.fetchone()
            
            if not customer:
                raise ValueError(f"Customer '{customer_name}' not found")
            
            customer = dict(customer)

            inv_id = None
            if invoice_number:
                c.execute("SELECT id, total_amount, paid_amount FROM invoices WHERE invoice_number=?",
                          (invoice_number,))
                inv = c.fetchone()
                if inv:
                    inv_id = inv['id']
                    new_paid = inv['paid_amount'] + amount
                    status = 'paid' if new_paid >= inv['total_amount'] else 'partial'
                    c.execute("UPDATE invoices SET paid_amount=?, status=? WHERE id=?",
                              (new_paid, status, inv_id))

            c.execute("""INSERT INTO payments
                         (owner_id, customer_id, customer_name, amount, payment_mode, utr_number, invoice_id)
                         VALUES (?,?,?,?,?,?,?)""",
                      (owner_id, customer['id'], customer['name'], amount,
                       payment_mode, utr_number, inv_id))

            c.execute("UPDATE customers SET outstanding_balance=outstanding_balance-? WHERE id=?",
                      (amount, customer['id']))
            c.execute("SELECT outstanding_balance FROM customers WHERE id=?", (customer['id'],))
            new_balance = c.fetchone()['outstanding_balance']

            c.execute("""INSERT INTO udhaar_ledger
                         (owner_id, customer_id, customer_name, transaction_type, amount, balance, description)
                         VALUES (?,?,?,'credit',?,?,?)""",
                      (owner_id, customer['id'], customer['name'], amount, new_balance,
                       f"Payment via {payment_mode}" + (f" UTR:{utr_number}" if utr_number else "")))

            c.execute("""INSERT INTO activity_log (owner_id, action_type, entity_type, details)
                         VALUES (?,?,?,?)""",
                      (owner_id, 'RECORD_PAYMENT', 'payment',
                       f"{customer_name} | ₹{amount} via {payment_mode}"))

            conn.commit()
            logger.info(f"Payment recorded: ₹{amount} from {customer_name}")
            return {"amount": amount, "new_balance": new_balance, "payment_mode": payment_mode}
        finally:
            conn.close()


# ==================== Reporting Functions ====================

def get_daily_summary(date: Optional[str] = None, owner_id: str = 'default') -> Dict[str, Any]:
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""SELECT COUNT(*) as count, COALESCE(SUM(total_amount),0) as total
                 FROM invoices WHERE DATE(invoice_date)=? AND owner_id=?""", (date, owner_id))
    sales = dict(c.fetchone())

    c.execute("""SELECT COUNT(*) as count, COALESCE(SUM(amount),0) as total
                 FROM payments WHERE DATE(payment_date)=? AND owner_id=?""", (date, owner_id))
    payments = dict(c.fetchone())

    c.execute("""SELECT COUNT(*) as count, COALESCE(SUM(amount),0) as total
                 FROM expenses WHERE DATE(expense_date)=? AND owner_id=?""", (date, owner_id))
    expenses = dict(c.fetchone())

    c.execute("SELECT COALESCE(SUM(outstanding_balance),0) as total FROM customers WHERE owner_id=?",
              (owner_id,))
    udhaar = c.fetchone()['total']
    conn.close()

    return {
        "date": date,
        "sales": sales,
        "payments": payments,
        "expenses": expenses,
        "outstanding_udhaar": udhaar,
        "net_cash_flow": payments['total'] - expenses['total']
    }


def get_overdue_customers(days: int = 14, owner_id: str = 'default') -> List[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT c.*, MAX(ul.transaction_date) as last_txn,
               CAST((julianday('now') - julianday(MAX(ul.transaction_date))) AS INTEGER) as days_overdue
        FROM customers c
        LEFT JOIN udhaar_ledger ul ON c.id=ul.customer_id
        WHERE c.outstanding_balance > 0 AND c.owner_id=?
        GROUP BY c.id
        ORDER BY c.outstanding_balance DESC
    """, (owner_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_weekly_summary(owner_id: str = 'default') -> Dict[str, Any]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT DATE(invoice_date) as day,
                        COUNT(*) as invoices, COALESCE(SUM(total_amount),0) as revenue
                 FROM invoices WHERE owner_id=? AND invoice_date >= date('now','-7 days')
                 GROUP BY day ORDER BY day""", (owner_id,))
    weekly = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"weekly_sales": weekly}


# ==================== Business Owner Functions ====================

def create_business_owner(phone: str, name: str, business_name: str, **kwargs) -> dict:
    """Create new business owner account"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Check if already exists
        c.execute("SELECT * FROM business_owners WHERE phone = ?", (phone,))
        existing = c.fetchone()
        if existing:
            raise ValueError("User already registered")
        
        c.execute("""
            INSERT INTO business_owners 
            (phone, name, business_name, business_address, business_gstin, business_upi_id, onboarding_complete)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (phone, name, business_name, 
              kwargs.get('business_address'), 
              kwargs.get('business_gstin'),
              kwargs.get('business_upi_id')))
        
        conn.commit()
        owner_id = c.lastrowid
        
        c.execute("SELECT * FROM business_owners WHERE id = ?", (owner_id,))
        owner = dict(c.fetchone())
        
        logger.info(f"Created business owner: {name} ({phone})")
        return owner
    finally:
        conn.close()


def get_business_owner(phone: str) -> Optional[Dict[str, Any]]:
    """Get business owner by phone"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM business_owners WHERE phone = ?", (phone,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_owner_onboarding_status(phone: str) -> dict:
    """Check if user has completed onboarding"""
    owner = get_business_owner(phone)
    
    if not owner:
        return {"exists": False, "onboarding_complete": False}
    
    return {
        "exists": True,
        "onboarding_complete": bool(owner.get('onboarding_complete')),
        "name": owner.get('name'),
        "business_name": owner.get('business_name')
    }


def update_business_owner(phone: str, **kwargs) -> dict:
    """Update business owner details"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'business_name', 'business_address', 'business_gstin', 'business_upi_id']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return get_business_owner(phone)
        
        values.append(phone)
        query = f"UPDATE business_owners SET {', '.join(fields)}, last_active = CURRENT_TIMESTAMP WHERE phone = ?"
        
        c.execute(query, values)
        conn.commit()
        
        return get_business_owner(phone)
    finally:
        conn.close()


# ==================== Warranty Tracking Functions ====================

def add_warranty_tracking(product_name: str, customer_name: str, 
                         warranty_months: int, invoice_id: Optional[int] = None,
                         owner_id: str = 'default') -> dict:
    """Track warranty for a sold product"""
    if warranty_months <= 0:
        return {"success": False, "error": "No warranty for this product"}
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Get product details
        c.execute("SELECT id, name FROM products WHERE name LIKE ? AND owner_id = ? LIMIT 1",
                 (f"%{product_name}%", owner_id))
        product = c.fetchone()
        if not product:
            return {"success": False, "error": f"Product '{product_name}' not found"}
        
        # Get customer details
        customer = get_customer_by_name(customer_name, owner_id)
        if not customer:
            return {"success": False, "error": f"Customer '{customer_name}' not found"}
        
        # Calculate expiry date
        from dateutil.relativedelta import relativedelta
        purchase_date = datetime.now()
        expiry_date = purchase_date + relativedelta(months=warranty_months)
        
        c.execute("""
            INSERT INTO warranty_tracking 
            (owner_id, product_id, product_name, customer_id, customer_name, 
             invoice_id, warranty_months, warranty_expiry_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (owner_id, product['id'], product['name'], customer['id'], 
              customer['name'], invoice_id, warranty_months, 
              expiry_date.strftime('%Y-%m-%d')))
        
        warranty_id = c.lastrowid
        conn.commit()
        
        logger.info(f"Warranty tracked: {product['name']} for {customer['name']} ({warranty_months} months)")
        
        return {
            "success": True,
            "warranty_id": warranty_id,
            "product_name": product['name'],
            "customer_name": customer['name'],
            "warranty_months": warranty_months,
            "expiry_date": expiry_date.strftime('%Y-%m-%d'),
            "days_remaining": (expiry_date - purchase_date).days
        }
    finally:
        conn.close()


def get_warranty_info(product_name: Optional[str] = None, 
                     customer_name: Optional[str] = None,
                     owner_id: str = 'default') -> List[Dict[str, Any]]:
    """Get warranty information"""
    conn = get_db_connection()
    c = conn.cursor()
    
    query = """
        SELECT w.*, 
               CAST((julianday(w.warranty_expiry_date) - julianday('now')) AS INTEGER) as days_remaining
        FROM warranty_tracking w
        WHERE w.owner_id = ?
    """
    params = [owner_id]
    
    if product_name:
        query += " AND w.product_name LIKE ?"
        params.append(f"%{product_name}%")
    
    if customer_name:
        query += " AND w.customer_name LIKE ?"
        params.append(f"%{customer_name}%")
    
    query += " ORDER BY w.warranty_expiry_date ASC"
    
    c.execute(query, params)
    warranties = []
    
    for row in c.fetchall():
        w = dict(row)
        days_remaining = w.get('days_remaining', 0)
        
        # Update status based on expiry
        if days_remaining < 0 and w['status'] == 'active':
            c.execute("UPDATE warranty_tracking SET status = 'expired' WHERE id = ?", (w['id'],))
            w['status'] = 'expired'
        
        w['expired'] = days_remaining < 0
        warranties.append(w)
    
    conn.commit()
    conn.close()
    return warranties


def get_active_warranties(owner_id: str = 'default') -> List[Dict[str, Any]]:
    """Get all active (non-expired) warranties"""
    warranties = get_warranty_info(owner_id=owner_id)
    return [w for w in warranties if not w.get('expired', False)]


def get_expiring_warranties(days: int = 30, owner_id: str = 'default') -> List[Dict[str, Any]]:
    """Get warranties expiring in next N days"""
    warranties = get_active_warranties(owner_id)
    return [w for w in warranties if 0 <= w.get('days_remaining', -1) <= days]


if __name__ == "__main__":
    init_database()
    print("Database initialized!")
    create_product("Vivo V29",  "VIVO-V29", stock=50, cost_price=25000, selling_price=29999, gst_rate=18, warranty_months=12)
    create_product("Samsung S23","SAM-S23",  stock=30, cost_price=45000, selling_price=54999, gst_rate=18, warranty_months=24)
    create_product("iPhone 15", "IP-15",    stock=20, cost_price=65000, selling_price=79999, gst_rate=18, warranty_months=12)
    create_product("OnePlus 12","OP-12",    stock=15, cost_price=55000, selling_price=64999, gst_rate=18, warranty_months=12)
    create_customer("Ramesh Kumar",  "+919876543210", address="Lajpat Nagar, Delhi")
    create_customer("Suresh Gupta",  "+919876543211", address="Karol Bagh, Delhi")
    create_customer("Priya Sharma",  "+919876543212", address="Connaught Place, Delhi")
    print("Sample data added!")
