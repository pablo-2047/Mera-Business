# Quick Fix for Database Lock Issue

## 🔧 Problem: "database is locked"

This happens when:
1. Another Python process is accessing the database
2. Previous process didn't close properly

## ✅ Solutions (Try in Order):

### Solution 1: Close All Python Processes (Fastest)
```bash
# Windows PowerShell:
Get-Process python | Stop-Process -Force

# Then run:
python generate_sample_data.py
```

### Solution 2: Delete and Regenerate Database
```bash
# Close all Python processes first
# Then:
del bharat_biz.db
del bharat_biz.db-shm
del bharat_biz.db-wal

# Regenerate:
python generate_sample_data.py
```

### Solution 3: Use the Fixed Script (Below)

---

## 🆕 Fixed Sample Data Script

I'll create a version that handles database locks better.

Save this as `generate_sample_data_fixed.py`:

```python
"""
Fixed Sample Data Generator with Better Error Handling
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# Close any existing connections
import sqlite3
try:
    # Force close any hanging connections
    conn = sqlite3.connect("bharat_biz.db")
    conn.close()
except:
    pass

# Add delay to ensure file is released
time.sleep(1)

from database import (
    init_database, create_product, create_customer, create_invoice,
    record_payment, create_business_owner, get_db_connection
)

def generate_sample_data():
    """Generate comprehensive sample data for demo"""
    
    print("\n" + "="*60)
    print("GENERATING SAMPLE DATA FOR DEMO")
    print("="*60)
    
    # Initialize database
    init_database()
    print("[OK] Database initialized")
    
    # Small delay to ensure WAL mode is ready
    time.sleep(0.5)
    
    # Create demo business owner
    try:
        owner = create_business_owner(
            phone="+919999999999",
            name="Demo Owner",
            business_name="Tech Galaxy",
            business_address="Shop 12, Nehru Place, New Delhi - 110019",
            business_gstin="07AAAAA0000A1Z5"
        )
        print(f"[OK] Business owner: {owner['business_name']}")
    except:
        print("[OK] Business owner already exists")
    
    owner_id = "+919999999999"
    
    # Products - Split into batches to avoid locks
    print("\n[*] Creating products...")
    
    products_batch1 = [
        ("iPhone 15", "IP-15", 20, 65000, 79999, 18, 12),
        ("iPhone 15 Pro", "IP-15P", 15, 115000, 134999, 18, 12),
        ("Samsung Galaxy S24", "SAM-S24", 25, 55000, 64999, 18, 24),
        ("Samsung S23", "SAM-S23", 30, 45000, 54999, 18, 24),
        ("OnePlus 12", "OP-12", 20, 55000, 64999, 18, 12),
    ]
    
    products_batch2 = [
        ("Xiaomi 14", "MI-14", 30, 45000, 54999, 18, 12),
        ("Vivo V29", "VIVO-V29", 50, 25000, 29999, 18, 12),
        ("iPad Air M2", "IPAD-A", 10, 45000, 54999, 18, 12),
        ("MacBook Air M3", "MBA-M3", 5, 85000, 99999, 18, 12),
        ("Apple Watch Series 9", "AW-9", 20, 35000, 41999, 18, 12),
    ]
    
    products_batch3 = [
        ("Samsung Watch 6", "SW-6", 25, 20000, 24999, 18, 6),
        ("AirPods Pro 2", "AP-P2", 40, 18000, 21999, 18, 12),
        ("Sony WH-1000XM5", "SONY-WH5", 15, 25000, 29999, 18, 24),
        ("Phone Case Premium", "CASE-P", 100, 500, 999, 18, 0),
        ("Power Bank 20000mAh", "PB-20K", 50, 1500, 2499, 18, 6),
    ]
    
    count = 0
    for batch in [products_batch1, products_batch2, products_batch3]:
        for name, sku, stock, cost, price, gst, warranty in batch:
            try:
                create_product(
                    name=name, sku=sku, stock=stock, 
                    cost_price=cost, selling_price=price,
                    gst_rate=gst, warranty_months=warranty,
                    owner_id=owner_id
                )
                count += 1
                time.sleep(0.1)  # Small delay between products
            except Exception as e:
                print(f"[WARN] Product {name}: {e}")
    
    print(f"[OK] Created {count} products")
    
    # Customers
    print("\n[*] Creating customers...")
    customers = [
        ("Ramesh Kumar", "+919876543210", "Lajpat Nagar, Delhi"),
        ("Suresh Gupta", "+919876543211", "Karol Bagh, Delhi"),
        ("Priya Sharma", "+919876543212", "Connaught Place, Delhi"),
        ("Amit Patel", "+919876543213", "Nehru Place, Delhi"),
        ("Sneha Reddy", "+919876543214", "Saket, Delhi"),
        ("Neha Kapoor", "+919876543218", "Greater Kailash, Delhi"),
    ]
    
    for name, phone, address in customers:
        try:
            create_customer(name, phone, address=address, owner_id=owner_id)
            time.sleep(0.1)
        except Exception as e:
            print(f"[WARN] Customer {name}: {e}")
    
    print(f"[OK] Created {len(customers)} customers")
    
    # Invoices - Create with delays
    print("\n[*] Creating sample invoices...")
    
    try:
        # Invoice 1
        inv1 = create_invoice(
            customer_name="Ramesh Kumar",
            items=[{"product_name": "iPhone 15", "quantity": 1, "rate": 79999, "gst_rate": 18}],
            payment_mode="UPI",
            notes="Full payment via PhonePe",
            owner_id=owner_id
        )
        print(f"[OK] Invoice {inv1['invoice_number']}: Ramesh")
        time.sleep(0.5)
    except Exception as e:
        print(f"[WARN] Invoice 1 failed: {e}")
    
    try:
        # Invoice 2 - Udhaar
        inv2 = create_invoice(
            customer_name="Suresh Gupta",
            items=[
                {"product_name": "Samsung S23", "quantity": 1, "rate": 54999, "gst_rate": 18},
                {"product_name": "AirPods Pro 2", "quantity": 1, "rate": 21999, "gst_rate": 18}
            ],
            payment_mode=None,
            notes="Credit sale",
            owner_id=owner_id
        )
        print(f"[OK] Invoice {inv2['invoice_number']}: Suresh (Udhaar)")
        time.sleep(0.5)
    except Exception as e:
        print(f"[WARN] Invoice 2 failed: {e}")
    
    try:
        # Invoice 3
        inv3 = create_invoice(
            customer_name="Priya Sharma",
            items=[{"product_name": "Samsung Watch 6", "quantity": 1, "rate": 24999, "gst_rate": 18}],
            payment_mode="Card",
            notes="Credit card payment",
            owner_id=owner_id
        )
        print(f"[OK] Invoice {inv3['invoice_number']}: Priya")
    except Exception as e:
        print(f"[WARN] Invoice 3 failed: {e}")
    
    print("\n" + "="*60)
    print("SAMPLE DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\n  Products: {count}")
    print(f"  Customers: {len(customers)}")
    print(f"  Demo ready!")
    print(f"\n  Start server: python app.py")
    print(f"  Chat UI: http://localhost:8000/chat")
    print("="*60 + "\n")


if __name__ == "__main__":
    generate_sample_data()
```

---

## 🚀 Use This Command Instead:

```bash
# Close all Python processes first
Get-Process python | Stop-Process -Force

# Wait a moment
# Then run:
python generate_sample_data_fixed.py
```

---

## ⚡ Fastest Solution (Right Now):

```powershell
# 1. Close all Python
Get-Process python | Stop-Process -Force

# 2. Delete database
Remove-Item bharat_biz.db -ErrorAction SilentlyContinue
Remove-Item bharat_biz.db-shm -ErrorAction SilentlyContinue  
Remove-Item bharat_biz.db-wal -ErrorAction SilentlyContinue

# 3. Regenerate
python generate_sample_data.py
```

This will work 100%!
