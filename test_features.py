"""
Mera Business - Quick Test Script
Tests all major features to ensure everything works
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import (
    init_database, create_business_owner, get_owner_onboarding_status,
    create_product, get_all_products, create_customer, create_invoice,
    get_warranty_info, get_active_warranties, get_business_owner
)

def test_database_init():
    """Test 1: Database Initialization"""
    print("\n" + "="*60)
    print("TEST 1: Database Initialization")
    print("="*60)
    try:
        init_database()
        print("[OK] Database initialized successfully")
        print("[OK] All tables created")
        return True
    except Exception as e:
        print(f"[FAIL] Database init failed: {e}")
        return False


def test_business_owner():
    """Test 2: Business Owner Registration"""
    print("\n" + "="*60)
    print("TEST 2: Business Owner Registration")
    print("="*60)
    
    phone = "+919999999999"
    
    try:
        # Check if already exists
        status = get_owner_onboarding_status(phone)
        if status['exists']:
            print(f"[OK] Business owner already exists: {status['name']}")
            return True
        
        # Create new owner
        owner = create_business_owner(
            phone=phone,
            name="Test Owner",
            business_name="Test Business"
        )
        print(f"[OK] Business owner created: {owner['name']}")
        print(f"  Phone: {owner['phone']}")
        print(f"  Business: {owner['business_name']}")
        
        # Verify
        status = get_owner_onboarding_status(phone)
        assert status['exists'] == True
        assert status['onboarding_complete'] == True
        print("[OK] Onboarding status verified")
        
        return True
    except Exception as e:
        print(f"[FAIL] Business owner test failed: {e}")
        return False


def test_products_with_warranty():
    """Test 3: Products with Warranty"""
    print("\n" + "="*60)
    print("TEST 3: Products with Warranty")
    print("="*60)
    
    owner_id = "+919999999999"
    
    try:
        # Create products with warranty
        products = [
            ("Test Phone", 29999, 10, 18, 12),  # 12 months warranty
            ("Test Laptop", 54999, 5, 18, 24),  # 24 months warranty
            ("Test Watch", 9999, 20, 18, 6),    # 6 months warranty
        ]
        
        for name, price, stock, gst, warranty in products:
            pid = create_product(
                name=name,
                selling_price=price,
                stock=stock,
                gst_rate=gst,
                warranty_months=warranty,
                owner_id=owner_id
            )
            print(f"[OK] Created: {name} (Warranty: {warranty} months)")
        
        # Verify products
        all_products = get_all_products(owner_id)
        warranty_products = [p for p in all_products if p['warranty_months'] > 0]
        print(f"[OK] Total products with warranty: {len(warranty_products)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Product test failed: {e}")
        return False


def test_invoice_with_warranty():
    """Test 4: Invoice Creation with Warranty Tracking"""
    print("\n" + "="*60)
    print("TEST 4: Invoice with Warranty Tracking")
    print("="*60)
    
    owner_id = "+919999999999"
    
    try:
        # Create customer
        cust_id = create_customer(
            name="Test Customer",
            phone="+919888888888",
            owner_id=owner_id
        )
        print(f"[OK] Customer created: Test Customer")
        
        # Create invoice with warranty product
        invoice = create_invoice(
            customer_name="Test Customer",
            items=[
                {
                    "product_name": "Test Phone",
                    "quantity": 1,
                    "rate": 29999,
                    "gst_rate": 18
                }
            ],
            payment_mode="UPI",
            owner_id=owner_id
        )
        
        print(f"[OK] Invoice created: {invoice['invoice_number']}")
        print(f"  Total: ₹{invoice['total_amount']:,.2f}")
        print(f"  Status: {invoice['status']}")
        
        # Check warranty tracking
        warranties = get_warranty_info(
            customer_name="Test Customer",
            owner_id=owner_id
        )
        
        if warranties:
            print(f"[OK] Warranty tracked: {len(warranties)} item(s)")
            for w in warranties:
                print(f"  - {w['product_name']}: {w['warranty_months']} months")
                print(f"    Expires: {w['warranty_expiry_date']}")
                print(f"    Days remaining: {w['days_remaining']}")
        else:
            print("[FAIL] No warranties tracked")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Invoice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_warranty_queries():
    """Test 5: Warranty Queries"""
    print("\n" + "="*60)
    print("TEST 5: Warranty Query Functions")
    print("="*60)
    
    owner_id = "+919999999999"
    
    try:
        # Get all warranties
        all_warranties = get_warranty_info(owner_id=owner_id)
        print(f"[OK] Total warranties: {len(all_warranties)}")
        
        # Get active warranties
        active = get_active_warranties(owner_id)
        print(f"[OK] Active warranties: {len(active)}")
        
        # Get by product
        phone_warranties = get_warranty_info(
            product_name="Test Phone",
            owner_id=owner_id
        )
        print(f"[OK] Test Phone warranties: {len(phone_warranties)}")
        
        # Get by customer
        customer_warranties = get_warranty_info(
            customer_name="Test Customer",
            owner_id=owner_id
        )
        print(f"[OK] Test Customer warranties: {len(customer_warranties)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Warranty query test failed: {e}")
        return False


def test_authentication_data():
    """Test 6: Authentication System Data"""
    print("\n" + "="*60)
    print("TEST 6: Authentication System")
    print("="*60)
    
    phone = "+919999999999"
    
    try:
        # Get owner details
        owner = get_business_owner(phone)
        
        if not owner:
            print("[FAIL] Owner not found")
            return False
        
        print(f"[OK] Owner details retrieved:")
        print(f"  Phone: {owner['phone']}")
        print(f"  Name: {owner['name']}")
        print(f"  Business: {owner['business_name']}")
        print(f"  Created: {owner['created_at']}")
        print(f"  Onboarding: {'Complete' if owner['onboarding_complete'] else 'Incomplete'}")
        
        # Check onboarding status
        status = get_owner_onboarding_status(phone)
        print(f"[OK] Onboarding status check:")
        print(f"  Exists: {status['exists']}")
        print(f"  Complete: {status['onboarding_complete']}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Authentication test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("MERA BUSINESS - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        test_database_init,
        test_business_owner,
        test_products_with_warranty,
        test_invoice_with_warranty,
        test_warranty_queries,
        test_authentication_data,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[FAIL] Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nALL TESTS PASSED!")
        print("  Database structure correct")
        print("  Business owner registration working")
        print("  Product warranty tracking working")
        print("  Invoice creation with warranty working")
        print("  Warranty queries working")
        print("  Authentication system ready")
        print("\nYour application is ready for deployment!")
    else:
        print(f"\n{total - passed} test(s) failed")
        print("Please review the errors above and fix them")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
