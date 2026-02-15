from database import get_daily_summary, get_overdue_customers, get_low_stock_products, get_all_products, get_all_invoices
import json

owner = '+919999999999'
print('SUMMARY:', json.dumps(get_daily_summary(owner_id=owner), indent=2))
print('UDHAAR:', json.dumps(get_overdue_customers(days=0, owner_id=owner), indent=2))
print('LOWSTOCK:', json.dumps(get_low_stock_products(owner), indent=2))
print('PRODUCTS:', json.dumps(get_all_products(owner), indent=2))
print('INVOICES:', json.dumps(get_all_invoices(owner)[:3], indent=2))
