"""
Bharat Biz-Agent - Database Layer
SQLite schema and utilities for business operations
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = "bharat_biz.db"


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Initialize SQLite database with all required tables
    
    Schema designed for Indian SMB operations:
    - Products: Inventory management
    - Customers: Customer ledger
    - Invoices: Sales records
    - Invoice Items: Line items in invoices
    - Payments: Payment tracking
    - Expenses: Business expenses
    - GST Records: Tax compliance
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Products/Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE,
        stock INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'piece',
        cost_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        gst_rate REAL DEFAULT 18.0,
        low_stock_alert INTEGER DEFAULT 10,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        email TEXT,
        address TEXT,
        gstin TEXT,
        outstanding_balance REAL DEFAULT 0,
        credit_limit REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Invoices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
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
    )
    """)
    
    # Invoice Items Table
    cursor.execute("""
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
        FOREIGN KEY (invoice_id) REFERENCES invoices (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)
    
    # Payments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
        payment_mode TEXT DEFAULT 'UPI',
        utr_number TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    """)
    
    # Expenses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT DEFAULT CURRENT_TIMESTAMP,
        payment_mode TEXT,
        vendor TEXT,
        gst_amount REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Udhaar (Credit) Ledger Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS udhaar_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        balance REAL NOT NULL,
        description TEXT,
        transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
        reminder_sent INTEGER DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    """)
    
    # GST Filings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gst_filings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    )
    """)
    
    # Activity Log Table (for audit trail)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        details TEXT,
        user_phone TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# ==================== Product Functions ====================

def create_product(name: str, sku: Optional[str] = None, stock: int = 0, 
                  cost_price: float = 0, selling_price: float = 0, 
                  gst_rate: float = 18.0, **kwargs) -> int:
    """
    Add a new product to inventory
    
    Args:
        name: Product name
        sku: Stock Keeping Unit (optional)
        stock: Initial stock quantity
        cost_price: Purchase/cost price
        selling_price: Selling price
        gst_rate: GST percentage (5, 12, 18, 28)
        
    Returns:
        Product ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO products (name, sku, stock, cost_price, selling_price, gst_rate, unit, low_stock_alert)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, sku or f"SKU{int(datetime.now().timestamp())}", stock, 
        cost_price, selling_price, gst_rate,
        kwargs.get('unit', 'piece'),
        kwargs.get('low_stock_alert', 10)
    ))
    
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"Created product: {name} (ID: {product_id})")
    return product_id


def update_inventory(product_name: str, quantity: int, operation: str = "reduce") -> Dict[str, Any]:
    """
    Update product inventory (add or reduce stock)
    
    Args:
        product_name: Name of product
        quantity: Quantity to add/reduce
        operation: "reduce" or "add"
        
    Returns:
        Updated product info
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find product
    cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{product_name}%",))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        raise ValueError(f"Product '{product_name}' not found")
    
    # Update stock
    if operation == "reduce":
        new_stock = max(0, product['stock'] - quantity)
    else:
        new_stock = product['stock'] + quantity
    
    cursor.execute("""
        UPDATE products 
        SET stock = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_stock, product['id']))
    
    conn.commit()
    
    # Get updated product
    cursor.execute("SELECT * FROM products WHERE id = ?", (product['id'],))
    updated_product = dict(cursor.fetchone())
    
    conn.close()
    
    logger.info(f"Updated inventory: {product_name} - {operation} {quantity}, new stock: {new_stock}")
    return updated_product


def get_low_stock_products() -> List[Dict[str, Any]]:
    """Get products below low stock alert threshold"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM products 
        WHERE stock <= low_stock_alert
        ORDER BY stock ASC
    """)
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return products


# ==================== Customer Functions ====================

def create_customer(name: str, phone: str, **kwargs) -> int:
    """
    Create or update customer record
    
    Args:
        name: Customer name
        phone: Phone number
        **kwargs: email, address, gstin, credit_limit
        
    Returns:
        Customer ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if customer exists
    cursor.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
    existing = cursor.fetchone()
    
    if existing:
        customer_id = existing['id']
        # Update existing
        cursor.execute("""
            UPDATE customers 
            SET name = ?, email = ?, address = ?, gstin = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, kwargs.get('email'), kwargs.get('address'), kwargs.get('gstin'), customer_id))
    else:
        # Create new
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address, gstin, credit_limit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, kwargs.get('email'), kwargs.get('address'), 
              kwargs.get('gstin'), kwargs.get('credit_limit', 0)))
        customer_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    logger.info(f"Customer record: {name} (ID: {customer_id})")
    return customer_id


def get_customer_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find customer by name (fuzzy match)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM customers WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1", 
                  (f"%{name}%",))
    customer = cursor.fetchone()
    conn.close()
    
    return dict(customer) if customer else None


# ==================== Invoice Functions ====================

def create_invoice(customer_name: str, items: List[Dict[str, Any]], 
                  payment_mode: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Create invoice with line items
    
    Args:
        customer_name: Name of customer
        items: List of dicts with {product_name, quantity, rate, gst_rate}
        payment_mode: UPI/Cash/Card (optional)
        notes: Additional notes
        
    Returns:
        Invoice details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get or create customer
    customer = get_customer_by_name(customer_name)
    if not customer:
        customer_id = create_customer(customer_name, phone=f"+91{int(datetime.now().timestamp()) % 10000000000}")
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = dict(cursor.fetchone())
    else:
        customer_id = customer['id']
    
    # Generate invoice number
    invoice_number = f"INV{datetime.now().strftime('%Y%m%d')}{int(datetime.now().timestamp()) % 10000}"
    
    # Calculate totals
    subtotal = 0
    gst_amount = 0
    
    for item in items:
        item_amount = item['quantity'] * item['rate']
        item_gst = item_amount * (item.get('gst_rate', 18) / 100)
        subtotal += item_amount
        gst_amount += item_gst
    
    total_amount = subtotal + gst_amount
    
    # Create invoice
    cursor.execute("""
        INSERT INTO invoices (invoice_number, customer_id, customer_name, subtotal, gst_amount, total_amount, payment_mode, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (invoice_number, customer_id, customer['name'], subtotal, gst_amount, total_amount, 
          payment_mode or 'pending', notes, 'paid' if payment_mode else 'pending'))
    
    invoice_id = cursor.lastrowid
    
    # Add invoice items and update inventory
    for item in items:
        cursor.execute("""
            INSERT INTO invoice_items (invoice_id, product_name, quantity, rate, gst_rate, amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (invoice_id, item['product_name'], item['quantity'], item['rate'], 
              item.get('gst_rate', 18), item['quantity'] * item['rate']))
        
        # Update inventory
        try:
            update_inventory(item['product_name'], int(item['quantity']), "reduce")
        except ValueError:
            logger.warning(f"Product not found in inventory: {item['product_name']}")
    
    # If not paid immediately, add to udhaar ledger
    if not payment_mode:
        cursor.execute("""
            INSERT INTO udhaar_ledger (customer_id, customer_name, transaction_type, amount, balance, description)
            VALUES (?, ?, 'debit', ?, ?, ?)
        """, (customer_id, customer['name'], total_amount, total_amount, f"Invoice {invoice_number}"))
        
        # Update customer outstanding
        cursor.execute("""
            UPDATE customers 
            SET outstanding_balance = outstanding_balance + ?
            WHERE id = ?
        """, (total_amount, customer_id))
    
    conn.commit()
    
    # Get complete invoice
    cursor.execute("""
        SELECT i.*, 
               GROUP_CONCAT(ii.product_name || ' x' || ii.quantity) as items_summary
        FROM invoices i
        LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
        WHERE i.id = ?
        GROUP BY i.id
    """, (invoice_id,))
    
    invoice = dict(cursor.fetchone())
    conn.close()
    
    logger.info(f"Created invoice: {invoice_number} for {customer_name}")
    return invoice


# ==================== Payment Functions ====================

def record_payment(customer_name: str, amount: float, payment_mode: str = "UPI", 
                  utr_number: Optional[str] = None, invoice_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Record a payment received from customer
    
    Args:
        customer_name: Name of customer
        amount: Payment amount
        payment_mode: UPI/Cash/Card
        utr_number: UTR/transaction reference
        invoice_number: Specific invoice (optional)
        
    Returns:
        Payment details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get customer
    customer = get_customer_by_name(customer_name)
    if not customer:
        conn.close()
        raise ValueError(f"Customer '{customer_name}' not found")
    
    # Get invoice if specified
    invoice_id = None
    if invoice_number:
        cursor.execute("SELECT id, total_amount, paid_amount FROM invoices WHERE invoice_number = ?", 
                      (invoice_number,))
        invoice = cursor.fetchone()
        if invoice:
            invoice_id = invoice['id']
            # Update invoice
            new_paid = invoice['paid_amount'] + amount
            status = 'paid' if new_paid >= invoice['total_amount'] else 'partial'
            cursor.execute("""
                UPDATE invoices 
                SET paid_amount = ?, status = ?
                WHERE id = ?
            """, (new_paid, status, invoice_id))
    
    # Record payment
    cursor.execute("""
        INSERT INTO payments (customer_id, customer_name, amount, payment_mode, utr_number, invoice_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer['id'], customer['name'], amount, payment_mode, utr_number, invoice_id))
    
    payment_id = cursor.lastrowid
    
    # Update customer outstanding
    cursor.execute("""
        UPDATE customers 
        SET outstanding_balance = outstanding_balance - ?
        WHERE id = ?
    """, (amount, customer['id']))
    
    # Add to udhaar ledger
    cursor.execute("""
        SELECT outstanding_balance FROM customers WHERE id = ?
    """, (customer['id'],))
    new_balance = cursor.fetchone()['outstanding_balance']
    
    cursor.execute("""
        INSERT INTO udhaar_ledger (customer_id, customer_name, transaction_type, amount, balance, description)
        VALUES (?, ?, 'credit', ?, ?, ?)
    """, (customer['id'], customer['name'], amount, new_balance, 
          f"Payment via {payment_mode}" + (f" - {utr_number}" if utr_number else "")))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Recorded payment: ₹{amount} from {customer_name}")
    return {"payment_id": payment_id, "amount": amount, "new_balance": new_balance}


# ==================== Reporting Functions ====================

def get_daily_summary(date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get daily business summary
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
        
    Returns:
        Summary with sales, payments, expenses
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total sales
    cursor.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM invoices
        WHERE DATE(invoice_date) = ?
    """, (date,))
    sales = dict(cursor.fetchone())
    
    # Total payments received
    cursor.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM payments
        WHERE DATE(payment_date) = ?
    """, (date,))
    payments = dict(cursor.fetchone())
    
    # Total expenses
    cursor.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE DATE(expense_date) = ?
    """, (date,))
    expenses = dict(cursor.fetchone())
    
    # Outstanding udhaar
    cursor.execute("""
        SELECT COALESCE(SUM(outstanding_balance), 0) as total
        FROM customers
    """)
    udhaar = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "date": date,
        "sales": sales,
        "payments": payments,
        "expenses": expenses,
        "outstanding_udhaar": udhaar,
        "net_cash_flow": payments['total'] - expenses['total']
    }


def get_overdue_customers(days: int = 30) -> List[Dict[str, Any]]:
    """
    Get customers with overdue payments
    
    Args:
        days: Days since last transaction
        
    Returns:
        List of customers with outstanding balance
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, 
               MAX(ul.transaction_date) as last_transaction_date,
               CAST((julianday('now') - julianday(MAX(ul.transaction_date))) AS INTEGER) as days_overdue
        FROM customers c
        LEFT JOIN udhaar_ledger ul ON c.id = ul.customer_id
        WHERE c.outstanding_balance > 0
        GROUP BY c.id
        HAVING days_overdue >= ?
        ORDER BY c.outstanding_balance DESC
    """, (days,))
    
    customers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return customers


if __name__ == "__main__":
    # Initialize database
    init_database()
    print("Database initialized successfully!")
    
    # Add sample data for testing
    print("\nAdding sample data...")
    
    # Sample products
    create_product("Vivo V29", "VIVO-V29", stock=50, cost_price=25000, selling_price=29999, gst_rate=18)
    create_product("Samsung S23", "SAM-S23", stock=30, cost_price=45000, selling_price=54999, gst_rate=18)
    create_product("iPhone 15", "IP-15", stock=20, cost_price=65000, selling_price=79999, gst_rate=18)
    
    print("✓ Added sample products")
    
    # Sample customer
    create_customer("Ramesh Kumar", "+919876543210", address="Market Road, Delhi")
    
    print("✓ Added sample customer")
    
    print("\nDatabase ready for use!")
