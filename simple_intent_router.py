"""
Mera Business — Offline Fallback Intent Router
Pattern-matching router used when Gemini API is unavailable.
No external dependencies — works 100% offline.
"""

import re
import logging
from typing import Optional

from database import (
    create_invoice, record_payment, update_inventory,
    get_daily_summary,
)

logger = logging.getLogger(__name__)


async def route_intent_and_execute_simple(text_content: str, owner_id: str = 'default') -> str:
    """
    Pattern-match Hindi/Hinglish/English → call DB function → return response.
    Used as automatic fallback when Gemini API call fails.
    """
    t = text_content.lower().strip()
    numbers = re.findall(r'\d+', text_content)

    # ── Invoice / Sale ───────────────────────────────────────────────────────
    if any(k in t for k in ['becha', 'beci', 'sold', 'invoice', 'bill bana']):
        try:
            words = text_content.split()
            customer_name = "Customer"
            for i, w in enumerate(words):
                if w.lower() in ('ko', 'ke') and i > 0:
                    customer_name = words[i - 1]
                    break

            amount = int(numbers[-1]) if numbers else 30000

            product_name = "Product"
            if 'samsung' in t or 's23' in t:
                product_name = "Samsung S23"
            elif 'iphone' in t:
                product_name = "iPhone 15"
            elif 'vivo' in t or 'v29' in t:
                product_name = "Vivo V29"

            payment_mode = "UPI" if 'upi' in t else ("Cash" if 'cash' in t else None)

            invoice = create_invoice(
                customer_name=customer_name,
                items=[{'product_name': product_name, 'quantity': 1,
                        'rate': amount, 'gst_rate': 18}],
                payment_mode=payment_mode,
                owner_id=owner_id
            )
            gst = invoice['gst_amount']
            total = invoice['total_amount']
            return (
                f"✅ Invoice created!\n"
                f"📄 {invoice['invoice_number']}\n"
                f"👤 Customer: {customer_name}\n"
                f"📦 {product_name} × 1\n"
                f"💰 ₹{amount:,.0f} + GST ₹{gst:,.2f} = ₹{total:,.2f}\n"
                f"{'💳 ' + payment_mode if payment_mode else '📝 Udhaar recorded'}"
            )
        except Exception as e:
            logger.error(f"Fallback invoice error: {e}")
            return f"Invoice बनाने में दिक्कत आई। Error: {e}"

    # ── Payment Received ──────────────────────────────────────────────────────
    if any(k in t for k in ['payment', 'paisa', 'diya', 'aaya', 'received']):
        try:
            words = text_content.split()
            customer_name = "Customer"
            for i, w in enumerate(words):
                if w.lower() in ('se', 'ne', 'from') and i > 0:
                    customer_name = words[i - 1]
                    break

            amount = int(numbers[0]) if numbers else 1000
            mode = "UPI" if 'upi' in t else ("Cash" if 'cash' in t else "UPI")
            utr = None
            if 'utr' in t and len(numbers) > 1:
                utr = numbers[1]

            result = record_payment(customer_name=customer_name, amount=amount,
                                    payment_mode=mode, utr_number=utr, owner_id=owner_id)
            return (
                f"✅ Payment recorded!\n"
                f"👤 {customer_name}\n"
                f"💰 ₹{amount:,.0f} via {mode}"
                + (f"\n🔖 UTR: {utr}" if utr else "")
                + f"\n📊 Outstanding: ₹{result['new_balance']:,.2f}"
            )
        except Exception as e:
            logger.error(f"Fallback payment error: {e}")
            return f"Payment record करने में दिक्कत आई। Error: {e}"

    # ── Daily Summary ─────────────────────────────────────────────────────────
    if any(k in t for k in ['hisaab', 'summary', 'हिसाब', 'report', 'aaj ka']):
        try:
            s = get_daily_summary(owner_id=owner_id)
            return (
                f"📊 आज का हिसाब ({s['date']})\n\n"
                f"💰 Sales   : {s['sales']['count']} invoices — ₹{s['sales']['total']:,.2f}\n"
                f"💸 Payments: {s['payments']['count']} received — ₹{s['payments']['total']:,.2f}\n"
                f"📉 Expenses: {s['expenses']['count']} — ₹{s['expenses']['total']:,.2f}\n"
                f"💵 Net Cash : ₹{s['net_cash_flow']:,.2f}\n"
                f"⚠️  Udhaar  : ₹{s['outstanding_udhaar']:,.2f}"
            )
        except Exception as e:
            logger.error(f"Fallback summary error: {e}")
            return f"Summary निकालने में दिक्कत आई। Error: {e}"

    # ── Inventory Add ─────────────────────────────────────────────────────────
    if 'stock' in t and any(k in t for k in ['add', 'daalo', 'jodo', 'increase']):
        try:
            product_name = "Vivo V29"
            if 'samsung' in t:
                product_name = "Samsung S23"
            elif 'iphone' in t:
                product_name = "iPhone 15"

            qty = int(numbers[0]) if numbers else 10
            p = update_inventory(product_name=product_name, quantity=qty, operation='add', owner_id=owner_id)
            return (
                f"✅ Stock updated!\n"
                f"📦 {product_name}\n"
                f"➕ Added: {qty} units\n"
                f"📊 New stock: {p['stock']} units"
            )
        except Exception as e:
            logger.error(f"Fallback inventory error: {e}")
            return f"Stock update करने में दिक्कत आई। Error: {e}"

    # ── Unknown ───────────────────────────────────────────────────────────────
    return (
        "मुझे समझ नहीं आया। कृपया इस तरह बताएं:\n\n"
        "📝 Invoice  : \"Ramesh ko Vivo becha 30000\"\n"
        "💰 Payment  : \"Ramesh se 5000 payment aaya UPI se\"\n"
        "📊 Summary  : \"Aaj ka hisaab batao\"\n"
        "📦 Stock    : \"Vivo ka 20 piece stock add karo\""
    )


async def route_intent_and_execute(
    text_content: str, media_path: Optional[str] = None,
    media_type: Optional[str] = None, owner_id: str = 'default'
) -> str:
    return await route_intent_and_execute_simple(text_content, owner_id=owner_id)
