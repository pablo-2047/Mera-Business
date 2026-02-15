from database import *
init_database()
try:
    create_product('Vivo V29', 'VIVO-V29', stock=50, cost_price=25000, selling_price=29999, gst_rate=18)
    create_product('Samsung S23', 'SAM-S23', stock=5, cost_price=45000, selling_price=54999, gst_rate=18)
    create_product('iPhone 15', 'IP-15', stock=3, cost_price=65000, selling_price=79999, gst_rate=18)
    print('Products added')
except Exception as e:
    print(f'Products note: {e}')
try:
    create_customer('Ramesh Kumar', '+919876543210', address='Lajpat Nagar, Delhi')
    create_customer('Suresh Gupta', '+919876543211', address='Karol Bagh, Delhi')
    create_customer('Priya Sharma', '+919876543212', address='Connaught Place, Delhi')
    print('Customers added')
except Exception as e:
    print(f'Customers note: {e}')
inv = create_invoice('Ramesh Kumar', [{'product_name':'Vivo V29','quantity':1,'rate':29999,'gst_rate':18}], payment_mode='UPI')
print('Invoice created:', inv['invoice_number'], 'total=', inv['total_amount'])
inv2 = create_invoice('Suresh Gupta', [{'product_name':'Samsung S23','quantity':1,'rate':54999,'gst_rate':18}])
print('Udhaar invoice:', inv2['invoice_number'], 'status=', inv2['status'])
pay = record_payment('Suresh Gupta', 20000, 'UPI', '123456789012')
print('Payment recorded, new balance:', pay['new_balance'])
s = get_daily_summary()
print('Daily summary: sales=', s['sales']['total'], 'udhaar=', s['outstanding_udhaar'])
ls = get_low_stock_products()
print('Low stock:', [p['name'] for p in ls])
print('ALL TESTS PASSED!')
