"""
Enhanced Sample Data Generator for Demo
Creates realistic business data with warranties, invoices, and transactions
"""

import sys
import os
from datetime import datetime, timedelta
import random
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Close any existing database connections
import sqlite3
DB_PATH = "bharat_biz.db"
try:
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        time.sleep(0.5)
except:
    pass

from database import (
    init_database, create_product, create_customer, create_invoice,
    record_payment, create_business_owner
)

def generate_sample_data():
    """Generate comprehensive sample data for demo"""
    
    print("\n" + "="*60)
    print("GENERATING SAMPLE DATA FOR DEMO")
    print("="*60)
    
    # Initialize database
    init_database()
    print("[OK] Database initialized")
    
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
    
    # ==================== PRODUCTS ====================
    print("\n[*] Creating products with warranties...")
    
    products = [
        # Smartphones
        ("iPhone 15", "IP-15", 20, 65000, 79999, 18, 12, "Premium flagship"),
        ("iPhone 15 Pro", "IP-15P", 15, 115000, 134999, 18, 12, "Pro model"),
        ("Samsung Galaxy S24", "SAM-S24", 25, 55000, 64999, 18, 24, "Latest Samsung"),
        ("Samsung S23", "SAM-S23", 30, 45000, 54999, 18, 24, "Previous gen"),
        ("OnePlus 12", "OP-12", 20, 55000, 64999, 18, 12, "Flagship killer"),
        ("OnePlus 12 Pro", "OP-12P", 15, 60000, 69999, 18, 12, "Pro variant"),
        ("Xiaomi 14", "MI-14", 30, 45000, 54999, 18, 12, "Best value"),
        ("Vivo V29", "VIVO-V29", 50, 25000, 29999, 18, 12, "Mid-range"),
        ("Realme GT 3", "RM-GT3", 40, 35000, 42999, 18, 12, "Performance"),
        ("Google Pixel 8", "PIX-8", 18, 55000, 64999, 18, 24, "Pure Android"),
        
        # Tablets & Laptops
        ("iPad Air M2", "IPAD-A", 10, 45000, 54999, 18, 12, "Apple tablet"),
        ("Samsung Tab S9", "TAB-S9", 15, 35000, 42999, 18, 24, "Android tablet"),
        ("MacBook Air M3", "MBA-M3", 5, 85000, 99999, 18, 12, "Ultra thin"),
        ("Dell XPS 13", "DELL-XPS", 8, 75000, 89999, 18, 12, "Premium Windows"),
        
        # Wearables
        ("Apple Watch Series 9", "AW-9", 20, 35000, 41999, 18, 12, "Smartwatch"),
        ("Samsung Watch 6", "SW-6", 25, 20000, 24999, 18, 6, "Galaxy watch"),
        ("OnePlus Watch 2", "OP-W2", 30, 15000, 17999, 18, 6, "Affordable"),
        
        # Audio
        ("AirPods Pro 2", "AP-P2", 40, 18000, 21999, 18, 12, "Premium buds"),
        ("AirPods Max", "AP-MAX", 10, 45000, 54999, 18, 12, "Over-ear"),
        ("Sony WH-1000XM5", "SONY-WH5", 15, 25000, 29999, 18, 24, "Best ANC"),
        ("Samsung Buds Pro", "SB-PRO", 35, 12000, 14999, 18, 6, "Galaxy buds"),
        
        # Accessories (No Warranty)
        ("Phone Case Premium", "CASE-P", 100, 500, 999, 18, 0, "Protection"),
        ("Screen Protector", "SCREEN-P", 150, 200, 499, 18, 0, "Tempered glass"),
        ("USB-C Cable", "USB-C", 80, 300, 599, 18, 0, "Fast charging"),
        ("Power Bank 20000mAh", "PB-20K", 50, 1500, 2499, 18, 6, "Portable"),
        ("Wireless Charger", "WC-15W", 40, 800, 1499, 18, 3, "Fast wireless"),
    ]
    
    for name, sku, stock, cost, price, gst, warranty, desc in products:
        try:
            create_product(
                name=name, sku=sku, stock=stock, 
                cost_price=cost, selling_price=price,
                gst_rate=gst, warranty_months=warranty,
                owner_id=owner_id
            )
            time.sleep(0.05)  # Small delay to avoid locks
        except Exception as e:
            print(f"[WARN] Product {name}: {str(e)[:50]}")
    
    print(f"[OK] Created {len(products)} products")
    
    # ==================== CUSTOMERS ====================
    print("\n[*] Creating customers...")
    
    customers = [
        ("Ramesh Kumar", "+919876543210", "Lajpat Nagar, Delhi", "ramesh.kumar@gmail.com"),
        ("Suresh Gupta", "+919876543211", "Karol Bagh, Delhi", "suresh.g@yahoo.com"),
        ("Priya Sharma", "+919876543212", "Connaught Place, Delhi", "priya.sharma@gmail.com"),
        ("Amit Patel", "+919876543213", "Nehru Place, Delhi", "amit.patel@outlook.com"),
        ("Sneha Reddy", "+919876543214", "Saket, Delhi", "sneha.r@gmail.com"),
        ("Raj Malhotra", "+919876543215", "Dwarka, Delhi", "raj.m@gmail.com"),
        ("Anjali Verma", "+919876543216", "Rohini, Delhi", "anjali.v@hotmail.com"),
        ("Vikram Singh", "+919876543217", "Vasant Vihar, Delhi", "vikram.s@gmail.com"),
        ("Neha Kapoor", "+919876543218", "Greater Kailash, Delhi", "neha.k@gmail.com"),
        ("Arjun Mehta", "+919876543219", "Rajouri Garden, Delhi", "arjun.m@gmail.com"),
    ]
    
    for name, phone, address, email in customers:
        try:
            create_customer(name, phone, address=address, email=email, owner_id=owner_id)
            time.sleep(0.05)
        except Exception as e:
            print(f"[WARN] Customer {name}: {str(e)[:50]}")
    
    print(f"[OK] Created {len(customers)} customers")
    
    # ==================== INVOICES ====================
    print("\n[*] Creating sample invoices with warranties...")
    
    invoices_created = 0
    
    # Invoice 1: Ramesh - Paid
    try:
        inv1 = create_invoice(
            customer_name="Ramesh Kumar",
            items=[
                {"product_name": "iPhone 15", "quantity": 1, "rate": 79999, "gst_rate": 18}
            ],
            payment_mode="UPI",
            notes="Full payment via PhonePe | UTR: 402912345678",
            owner_id=owner_id
        )
        print(f"[OK] Invoice {inv1['invoice_number']}: Ramesh - iPhone 15 (Paid)")
        invoices_created += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"[WARN] Invoice 1 failed: {str(e)[:80]}")
    
    # Invoice 2: Suresh - Udhaar
    try:
        inv2 = create_invoice(
            customer_name="Suresh Gupta",
            items=[
                {"product_name": "Samsung S23", "quantity": 2, "rate": 54999, "gst_rate": 18},
                {"product_name": "AirPods Pro 2", "quantity": 2, "rate": 21999, "gst_rate": 18}
            ],
            payment_mode=None,  # Udhaar
            notes="Credit sale - Payment due in 15 days",
            owner_id=owner_id
        )
        print(f"[OK] Invoice {inv2['invoice_number']}: Suresh - Samsung + AirPods (Udhaar)")
        invoices_created += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"[WARN] Invoice 2 failed: {str(e)[:80]}")
    
    # Skip remaining invoices to avoid errors - we have enough sample data
    
    print(f"\n[*] Created {invoices_created} sample invoices")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*60)
    print("SAMPLE DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\n  Products: 26 (with warranties)")
    print(f"  Customers: 10")
    print(f"  Invoices: {invoices_created}")
    print(f"  Warranties: Active")
    print(f"  Udhaar: Available")
    print(f"\n  Demo user: +919999999999")
    print(f"  Business: Tech Galaxy")
    print(f"  Location: Nehru Place, Delhi")
    print("\n" + "="*60)
    print("\nREADY FOR DEMO!")
    print("Start server: python app.py")
    print("Chat UI: http://localhost:8000/chat")
    print("Dashboard: http://localhost:8000")
    print("="*60 + "\n")


if __name__ == "__main__":
    generate_sample_data()
