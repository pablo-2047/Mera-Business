"""Seed rich demo data: invoices, udhaar, payments"""
import sqlite3
from datetime import datetime, timedelta
import random

DB = 'bharat_biz.db'
OWNER = '+919999999999'

conn = sqlite3.connect(DB)
c = conn.cursor()

# Clear existing invoice/payment data for clean demo
c.execute("DELETE FROM invoices WHERE owner_id=?", (OWNER,))
c.execute("UPDATE customers SET outstanding_balance=0 WHERE owner_id=?", (OWNER,))
conn.commit()

# Get customers and products
c.execute("SELECT id, name FROM customers WHERE owner_id=? LIMIT 10", (OWNER,))
customers = c.fetchall()
c.execute("SELECT id, name, selling_price, gst_rate FROM products WHERE owner_id=? LIMIT 8", (OWNER,))
products = c.fetchall()

now = datetime.now()

# --- PAID INVOICES (last 7 days) for weekly chart ---
paid_invoices = [
    (customers[0], products[0], 7, 'cash', 6),   # Ramesh, iPhone 15, 6 days ago
    (customers[1], products[2], 1, 'upi', 5),    # Suresh, Samsung S24
    (customers[2], products[4], 2, 'upi', 4),    # Priya, OnePlus 12
    (customers[3], products[1], 1, 'card', 3),   # Amit, iPhone 15 Pro
    (customers[4], products[2], 1, 'cash', 2),   # Sneha, Samsung S24
    (customers[5], products[3], 2, 'upi', 1),    # Raj, Samsung S23
    (customers[6], products[0], 1, 'cash', 0),   # Anjali, iPhone 15 (today)
]

for i, (cust, prod, qty, mode, days_ago) in enumerate(paid_invoices):
    inv_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    subtotal = prod[2] * qty
    gst = subtotal * (prod[3]/100)
    total = subtotal + gst
    inv_num = f"INV-2026-{100+i:03d}"
    c.execute("""INSERT INTO invoices 
        (owner_id, invoice_number, customer_id, customer_name, invoice_date, due_date,
         subtotal, gst_amount, total_amount, paid_amount, status, payment_mode, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (OWNER, inv_num, cust[0], cust[1], inv_date,
         (now - timedelta(days=days_ago-7)).strftime('%Y-%m-%d'),
         subtotal, gst, total, total, 'paid', mode,
         (now - timedelta(days=days_ago)).isoformat()))
    print(f"  Paid: {inv_num} {cust[1]} {prod[1]} x{qty} Rs{total:.0f} ({days_ago}d ago)")

# --- UDHAAR INVOICES (unpaid) ---
udhaar_invoices = [
    (customers[7], products[0], 1, 15),   # Vikram, iPhone 15, 15 days overdue
    (customers[8], products[1], 1, 30),   # Neha, iPhone 15 Pro, 30 days overdue
    (customers[9], products[2], 2, 7),    # Arjun, Samsung S24, 7 days
    (customers[0], products[4], 1, 45),   # Ramesh again, 45 days
    (customers[1], products[3], 3, 20),   # Suresh, Samsung S23
]

for i, (cust, prod, qty, days_ago) in enumerate(udhaar_invoices):
    inv_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    due_date = (now - timedelta(days=days_ago-14)).strftime('%Y-%m-%d')  # was due 14 days after sale
    subtotal = prod[2] * qty
    gst = subtotal * (prod[3]/100)
    total = subtotal + gst
    inv_num = f"INV-2026-{200+i:03d}"
    c.execute("""INSERT INTO invoices 
        (owner_id, invoice_number, customer_id, customer_name, invoice_date, due_date,
         subtotal, gst_amount, total_amount, paid_amount, status, payment_mode, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (OWNER, inv_num, cust[0], cust[1], inv_date, due_date,
         subtotal, gst, total, 0, 'pending', None,
         (now - timedelta(days=days_ago)).isoformat()))
    # Update customer outstanding balance
    c.execute("UPDATE customers SET outstanding_balance = outstanding_balance + ? WHERE id=?",
              (total, cust[0]))
    print(f"  Udhaar: {inv_num} {cust[1]} {prod[1]} x{qty} Rs{total:.0f} ({days_ago}d ago)")

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM invoices WHERE owner_id=?", (OWNER,))
print(f"\nTotal invoices: {c.fetchone()[0]}")
c.execute("SELECT name, outstanding_balance FROM customers WHERE owner_id=? AND outstanding_balance>0", (OWNER,))
udh = c.fetchall()
print(f"Customers with udhaar: {udh}")
conn.close()
print("\nDone! Demo data seeded.")
