"""
Simple Intent Router - WITHOUT Function Calling
Uses direct prompting instead of function calling for compatibility
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except Exception as e:
    GEMINI_AVAILABLE = False
    print(f"Gemini not available: {e}")

from database import (
    create_invoice, record_payment, update_inventory,
    get_daily_summary, create_product, create_customer
)

logger = logging.getLogger(__name__)


async def route_intent_and_execute_simple(text_content: str) -> str:
    """
    Simplified version without function calling
    Parses text directly and calls functions
    """
    
    text_lower = text_content.lower()
    
    # Pattern matching for common operations
    
    # Invoice creation: "Ramesh ko phone becha 30000"
    if 'becha' in text_lower or 'sold' in text_lower or 'invoice' in text_lower or 'bill' in text_lower:
        try:
            # Extract customer name (word before 'ko')
            words = text_content.split()
            customer_idx = -1
            for i, word in enumerate(words):
                if 'ko' in word.lower():
                    customer_idx = i
                    break
            
            if customer_idx > 0:
                customer_name = words[customer_idx - 1]
            else:
                customer_name = "Customer"
            
            # Extract amount (look for numbers)
            import re
            amounts = re.findall(r'\d+', text_content)
            amount = int(amounts[-1]) if amounts else 30000
            
            # Determine product (simple logic)
            product_name = "Vivo V29"  # Default
            if 'samsung' in text_lower or 's23' in text_lower:
                product_name = "Samsung S23"
                amount = amount or 54999
            elif 'iphone' in text_lower or '15' in text_lower:
                product_name = "iPhone 15"
                amount = amount or 79999
            elif 'vivo' in text_lower or 'v29' in text_lower:
                product_name = "Vivo V29"
                amount = amount or 29999
            
            # Create invoice
            invoice = create_invoice(
                customer_name=customer_name,
                items=[{
                    'product_name': product_name,
                    'quantity': 1,
                    'rate': amount,
                    'gst_rate': 18
                }],
                payment_mode='UPI' if 'upi' in text_lower else None
            )
            
            total = invoice['total_amount']
            gst = invoice['gst_amount']
            
            return f"""✅ Invoice created!
📄 {invoice['invoice_number']}
👤 Customer: {customer_name}
📱 Product: {product_name}
💰 Amount: ₹{amount:,.2f}
📊 GST (18%): ₹{gst:,.2f}
💵 Total: ₹{total:,.2f}
📦 Stock updated!"""
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return f"क्षमा करें, invoice create करने में error आया: {str(e)}"
    
    # Payment recording: "Ramesh se 5000 payment aaya"
    elif 'payment' in text_lower or 'paisa' in text_lower or 'पैसे' in text_lower:
        try:
            # Extract customer name
            words = text_content.split()
            customer_idx = -1
            for i, word in enumerate(words):
                if 'se' in word.lower():
                    customer_idx = i
                    break
            
            if customer_idx > 0:
                customer_name = words[customer_idx - 1]
            else:
                customer_name = "Customer"
            
            # Extract amount
            import re
            amounts = re.findall(r'\d+', text_content)
            amount = int(amounts[0]) if amounts else 5000
            
            # Record payment
            payment = record_payment(
                customer_name=customer_name,
                amount=amount,
                payment_mode='UPI' if 'upi' in text_lower else 'Cash'
            )
            
            return f"""✅ Payment recorded!
💰 Amount: ₹{amount:,.2f}
👤 Customer: {customer_name}
💳 Mode: {'UPI' if 'upi' in text_lower else 'Cash'}
📊 New Outstanding: ₹{payment['new_balance']:,.2f}"""
            
        except Exception as e:
            logger.error(f"Error recording payment: {e}")
            return f"क्षमा करें, payment record करने में error आया: {str(e)}"
    
    # Daily summary: "Aaj ka hisaab"
    elif 'hisaab' in text_lower or 'summary' in text_lower or 'हिसाब' in text_lower:
        try:
            summary = get_daily_summary()
            
            return f"""📊 आज का हिसाब ({summary['date']})

💰 Sales: {summary['sales']['count']} invoices - ₹{summary['sales']['total']:,.2f}
💸 Payments: {summary['payments']['count']} received - ₹{summary['payments']['total']:,.2f}
📉 Expenses: {summary['expenses']['count']} - ₹{summary['expenses']['total']:,.2f}
💵 Net Cash Flow: ₹{summary['net_cash_flow']:,.2f}
⚠️  Outstanding Udhaar: ₹{summary['outstanding_udhaar']:,.2f}"""
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return f"क्षमा करें, summary निकालने में error आया: {str(e)}"
    
    # Stock update: "iPhone ka stock 5 add karo"
    elif 'stock' in text_lower and ('add' in text_lower or 'karo' in text_lower):
        try:
            # Extract product
            product_name = "Vivo V29"  # Default
            if 'samsung' in text_lower or 's23' in text_lower:
                product_name = "Samsung S23"
            elif 'iphone' in text_lower:
                product_name = "iPhone 15"
            
            # Extract quantity
            import re
            quantities = re.findall(r'\d+', text_content)
            quantity = int(quantities[0]) if quantities else 5
            
            # Update inventory
            product = update_inventory(
                product_name=product_name,
                quantity=quantity,
                operation='add'
            )
            
            return f"""✅ Inventory updated!
📱 Product: {product_name}
➕ Added: {quantity} pieces
📦 New Stock: {product['stock']} units"""
            
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            return f"क्षमा करें, stock update करने में error आया: {str(e)}"
    
    else:
        # Generic response
        return f"""मुझे समझ नहीं आया। कृपया कोशिश करें:

📝 Invoice: "Ramesh ko phone becha 30000 mein"
💰 Payment: "Ramesh se 5000 payment aaya UPI se"
📊 Summary: "Aaj ka hisaab batao"
📦 Stock: "iPhone ka stock 5 add karo"
"""


# Alias for compatibility
async def route_intent_and_execute(text_content: str, media_path=None, media_type=None) -> str:
    """Wrapper for compatibility"""
    return await route_intent_and_execute_simple(text_content)
