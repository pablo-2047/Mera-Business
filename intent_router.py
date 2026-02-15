"""
Mera Business — Production Intent Router
Gemini 2.5 Flash with Context Caching + Function Calling + UPI Screenshot OCR
"""

import os, logging, json, base64
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from database import (
    create_invoice, record_payment, update_inventory, create_product,
    create_customer, get_daily_summary, get_customer_by_name,
    get_overdue_customers, get_low_stock_products, get_all_products,
    get_all_customers, get_warranty_info, get_all_invoices,
)

logger = logging.getLogger(__name__)
GEMINI_MODEL = 'gemini-2.5-flash'
_cache_instance = None

SYSTEM_INSTRUCTION = """तुम "Mera Business" हो — एक smart AI business assistant जो Indian shop owners की मदद करता है।

तुम्हारा काम है:
• Users के messages को समझना (Hindi, Hinglish, English — जो भी बोलें)
• Business operations execute करना — invoices बनाना, payments record करना, stock manage करना
• Natural और friendly response देना — user की language में

Business Terms Dictionary:
• "बेचा / becha / sold / diya" → create_invoice (with payment_mode)
• "उधार / udhaar / credit / baaki" → create_invoice (NO payment_mode = udhaar)
• "payment आया / mila / received / diya" → record_payment
• "stock add / daalo / increase / आया" → update_inventory (operation=add)
• "हिसाब / summary / report / aaj ka" → get_daily_summary
• "stock check / kitna hai / stock dikhao" → get_low_stock_alert
• "kaun pay nahi kiya / overdue / baaki" → get_overdue_reminders
• "invoice bhejo / send invoice" → send_invoice_to_customer
• "warranty check / warranty kitna hai" → get_warranty_info
• "rate kya hai / price / kitne ka / cost" → get_product_info (ALWAYS call this, never guess price)
• "kitne beche / sales / invoice history / kya becha" → get_sales_history
• "product list / inventory / stock dikhao / kya hai" → get_product_info

CRITICAL RULES:
• NEVER make up or guess product prices — ALWAYS call get_product_info first
• NEVER make up sales numbers — ALWAYS call get_sales_history first
• If you don't know something about THIS shop's data, call the appropriate function

Product Warranty:
• When adding products, shopkeeper can specify warranty period in months
• When product is sold, warranty is automatically tracked
• User can ask "Warranty kitni bachi hai?" or "iPhone ka warranty check karo"
• Show warranty expiry date and days remaining

Invoice Delivery:
• When shopkeeper asks to send invoice to customer, ask for customer's phone number
• Example: "Ramesh ko invoice bhejo +919876543210"
• Generate PDF and send via WhatsApp to customer

GST Rules (auto-apply):
• Electronics/Mobile: 18%
• Clothing/Textile: 5% or 12%
• Food/Grocery: 0% or 5%
• Luxury goods: 28%

Response Format Rules:
• Use ✅ for success, ❌ for errors, ⚠️ for warnings
• Amounts always as ₹XX,XXX format
• Dates as DD/MM/YYYY
• Keep responses SHORT and ACTION-ORIENTED — not long paragraphs
• Match the user's language (Hindi → Hindi, English → English, Hinglish → Hinglish)

ACTION RULES — VERY IMPORTANT:
• If user says "Ramesh ko Samsung S23 becha" → create_invoice immediately, qty=1, use DB price
• If user says "ek phone becha" in context of a conversation where phone model is already known → use that model
• NEVER ask for customer phone number unless user explicitly says "invoice bhejo" or "send invoice"
• NEVER ask for GST rate — use 18% for electronics automatically
• NEVER ask to confirm before creating an invoice — just do it and show the result
• If qty not mentioned → assume 1
• If price not mentioned → call get_product_info to look it up from DB, never guess
• Only ask ONE follow-up question maximum if truly something is missing (customer name or product name)"""

TOOL_LIST = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="create_invoice",
            description="Create sales invoice when customer buys something. Use payment_mode=None for udhaar/credit sales.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "customer_name": types.Schema(type=types.Type.STRING, description="Customer name"),
                    "items": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "product_name": types.Schema(type=types.Type.STRING),
                                "quantity":     types.Schema(type=types.Type.NUMBER),
                                "rate":         types.Schema(type=types.Type.NUMBER),
                                "gst_rate":     types.Schema(type=types.Type.NUMBER,
                                                             description="5/12/18/28 — default 18"),
                            },
                            required=["product_name", "quantity", "rate"]
                        )
                    ),
                    "payment_mode": types.Schema(type=types.Type.STRING,
                                                 description="UPI/Cash/Card — omit for udhaar"),
                    "notes": types.Schema(type=types.Type.STRING),
                },
                required=["customer_name", "items"]
            )
        ),
        types.FunctionDeclaration(
            name="record_payment",
            description="Record payment received from a customer",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "customer_name": types.Schema(type=types.Type.STRING),
                    "amount":        types.Schema(type=types.Type.NUMBER),
                    "payment_mode":  types.Schema(type=types.Type.STRING,
                                                  description="UPI/Cash/Card"),
                    "utr_number":    types.Schema(type=types.Type.STRING,
                                                  description="UTR or transaction ID"),
                },
                required=["customer_name", "amount"]
            )
        ),
        types.FunctionDeclaration(
            name="update_inventory",
            description="Add or reduce product stock",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(type=types.Type.STRING),
                    "quantity":     types.Schema(type=types.Type.NUMBER),
                    "operation":    types.Schema(type=types.Type.STRING,
                                                 description="add or reduce"),
                },
                required=["product_name", "quantity"]
            )
        ),
        types.FunctionDeclaration(
            name="create_product",
            description="Add a new product to the shop inventory with optional warranty",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name":            types.Schema(type=types.Type.STRING),
                    "selling_price":   types.Schema(type=types.Type.NUMBER),
                    "stock":           types.Schema(type=types.Type.NUMBER),
                    "gst_rate":        types.Schema(type=types.Type.NUMBER),
                    "cost_price":      types.Schema(type=types.Type.NUMBER),
                    "warranty_months": types.Schema(type=types.Type.NUMBER,
                                                   description="Warranty period in months (0 for no warranty)"),
                },
                required=["name", "selling_price"]
            )
        ),
        types.FunctionDeclaration(
            name="get_daily_summary",
            description="Get today's sales, payments, expenses and udhaar summary",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        ),
        types.FunctionDeclaration(
            name="get_customer_details",
            description="Get customer balance, outstanding udhaar, and transaction history",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"customer_name": types.Schema(type=types.Type.STRING)},
                required=["customer_name"]
            )
        ),
        types.FunctionDeclaration(
            name="get_overdue_reminders",
            description="List customers who haven't paid for a long time",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"days": types.Schema(type=types.Type.NUMBER,
                                                 description="Minimum days overdue (default 14)")},
            )
        ),
        types.FunctionDeclaration(
            name="get_low_stock_alert",
            description="Get products running low on stock",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        ),
        types.FunctionDeclaration(
            name="get_product_info",
            description="Look up price, stock, GST rate of a specific product or all products. Use this whenever user asks about price, rate, stock of any product.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(type=types.Type.STRING,
                                                 description="Product name to search (partial match ok). Leave empty to get all products."),
                },
            )
        ),
        types.FunctionDeclaration(
            name="get_sales_history",
            description="Get recent invoices/sales history. Use when user asks how many units sold, sales of a product, invoice list, recent transactions.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(type=types.Type.STRING,
                                                 description="Filter by product name (optional)"),
                    "customer_name": types.Schema(type=types.Type.STRING,
                                                  description="Filter by customer name (optional)"),
                },
            )
        ),
        types.FunctionDeclaration(
            name="send_invoice_to_customer",
            description="Send invoice PDF to customer via WhatsApp",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "invoice_number": types.Schema(type=types.Type.STRING,
                                                  description="Invoice number (e.g., INV20260215-0001)"),
                    "customer_phone": types.Schema(type=types.Type.STRING,
                                                  description="Customer's phone number with country code (+91XXXXXXXXXX)"),
                },
                required=["invoice_number", "customer_phone"]
            )
        ),
        types.FunctionDeclaration(
            name="get_warranty_info",
            description="Get warranty information for products or customers",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name":   types.Schema(type=types.Type.STRING,
                                                  description="Product name to filter warranty (optional)"),
                    "customer_name":  types.Schema(type=types.Type.STRING,
                                                  description="Customer name to filter warranty (optional)"),
                },
            )
        ),
    ])
]


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


def _get_or_create_cache(client: genai.Client):
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance
    try:
        _cache_instance = client.caches.create(
            model=GEMINI_MODEL,
            config=types.CreateCachedContentConfig(
                display_name='mera_business_v2',
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOL_LIST,
                ttl="3600s",
            )
        )
        logger.info(f"Context Cache created: {_cache_instance.name}")
    except Exception as e:
        logger.warning(f"Context caching unavailable: {e}")
        _cache_instance = "DISABLED"
    return _cache_instance


async def verify_upi_screenshot(image_path: str, owner_id: str = 'default') -> str:
    """
    Use Gemini Vision to OCR a UPI payment screenshot and cross-check against open invoices.
    """
    try:
        client = _get_client()
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        # Detect mime type from extension
        ext = image_path.lower().split('.')[-1]
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part(inline_data=types.Blob(mime_type=mime,
                                                   data=base64.b64encode(img_bytes).decode())),
                types.Part(text="""This is a UPI payment screenshot from an Indian payment app
                (GPay/PhonePe/Paytm/etc). Extract ONLY these fields as JSON:
                {
                  "amount": <number, in rupees>,
                  "utr": "<UTR or transaction ID string>",
                  "sender_name": "<name of person who sent money>",
                  "date": "<date shown>",
                  "app": "<payment app name>",
                  "status": "<Success/Failed/Pending>"
                }
                If any field is not visible, use null. Return ONLY the JSON, nothing else.""")
            ]
        )

        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        payment_data = json.loads(raw)

        amount = payment_data.get("amount")
        utr = payment_data.get("utr")
        sender = payment_data.get("sender_name") or "Unknown"
        status = payment_data.get("status", "Success")

        if status and "fail" in str(status).lower():
            return f"❌ Payment FAILED!\nScreenshot दिखाता है कि payment fail हुई।\nAmount: ₹{amount}"

        # Try to find matching customer
        customer = get_customer_by_name(sender, owner_id) if sender and sender != "Unknown" else None

        reply = f"📱 UPI Payment Detected!\n"
        reply += f"💰 Amount: ₹{amount:,.2f}\n" if amount else "💰 Amount: Not readable\n"
        reply += f"👤 Sender: {sender}\n"
        reply += f"🔖 UTR: {utr}\n" if utr else ""
        reply += f"✅ Status: {status}\n"

        if customer and amount:
            reply += f"\n🎯 Match found: {customer['name']}\n"
            reply += f"📊 Current outstanding: ₹{customer['outstanding_balance']:,.2f}\n"
            reply += f"\nKya main ₹{amount:,.0f} automatically record kar dun? (haan/nahi)"
        elif amount:
            reply += f"\nKis customer ka payment hai? Naam batao aur main record kar dunga."

        return reply

    except json.JSONDecodeError:
        return f"📱 Payment screenshot mila! OCR result:\n{response.text}\n\nKis customer ka payment hai? Manually batao."
    except Exception as e:
        logger.error(f"UPI screenshot error: {e}", exc_info=True)
        return "Screenshot process nahi ho paya. Kripya manually amount batayein."


async def route_intent_and_execute(
    text_content: str,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None,
    owner_id: str = 'default',
    conversation_history: list = None,
) -> str:
    if not text_content and not media_path:
        return "मुझे कुछ समझ नहीं आया। कृपया दोबारा बताएं।"

    # UPI Screenshot handling
    if media_path and media_type == "image":
        return await verify_upi_screenshot(media_path, owner_id)

    client = _get_client()
    _get_or_create_cache(client)  # warm cache attempt (free tier may reject, that's ok)

    # Build current user message parts
    current_parts = []
    if media_path and media_type == "audio":
        with open(media_path, "rb") as f:
            ext = media_path.lower().split('.')[-1]
            mime = {"ogg": "audio/ogg", "mp3": "audio/mpeg",
                    "amr": "audio/amr", "wav": "audio/wav"}.get(ext, "audio/ogg")
            current_parts.append(types.Part(inline_data=types.Blob(
                mime_type=mime, data=base64.b64encode(f.read()).decode()
            )))
    if text_content:
        current_parts.append(types.Part(text=text_content))

    # Build full contents list: history + current message
    # COST OPTIMIZATION: Only send last 6 messages (3 turns) as context.
    # Beyond that, context is rarely needed for shop commands and just burns tokens.
    contents = []
    if conversation_history and len(conversation_history) > 0:
        recent = conversation_history[-6:]  # last 3 user + 3 AI turns
        for msg in recent:
            role = "user" if msg["type"] == "sent" else "model"
            # Truncate long AI responses to 300 chars to save tokens
            content = msg["content"]
            if role == "model" and len(content) > 300:
                content = content[:300] + "…"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=content)]
            ))
    contents.append(types.Content(role="user", parts=current_parts))

    try:
        cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION, tools=TOOL_LIST, temperature=0.7)

        # Agentic loop — Gemini can chain multiple function calls (e.g. get_product_info → create_invoice)
        MAX_STEPS = 6
        for step in range(MAX_STEPS):
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=cfg
            )

            candidate = response.candidates[0].content

            # Collect all function calls in this response
            fn_calls = [p for p in candidate.parts
                        if hasattr(p, "function_call") and p.function_call]
            text_parts = [p for p in candidate.parts
                          if hasattr(p, "text") and p.text]

            if not fn_calls:
                # No more function calls — return the text response
                return "\n".join(p.text for p in text_parts) or "मुझे समझ नहीं आया। कृपया फिर से बताएं।"

            # Execute all function calls and collect results
            fn_result_parts = []
            for part in fn_calls:
                fn   = part.function_call.name
                args = dict(part.function_call.args) if part.function_call.args else {}
                args['owner_id'] = owner_id
                logger.info(f"[Step {step+1}] Function call: {fn}({args})")
                result = _execute_function(fn, args)
                fn_result_parts.append(
                    types.Part(function_response=types.FunctionResponse(
                        name=fn, response={"result": str(result)}
                    ))
                )

            # Append model's function call turn + our results to contents, then loop
            contents.append(types.Content(role="model", parts=fn_calls))
            contents.append(types.Content(role="user",  parts=fn_result_parts))

        return "प्रक्रिया पूरी नहीं हुई। कृपया फिर से बताएं।"

    except Exception as e:
        logger.error(f"Intent routing error: {e}", exc_info=True)
        from simple_intent_router import route_intent_and_execute_simple
        return await route_intent_and_execute_simple(text_content, owner_id=owner_id)


async def send_invoice_to_customer_impl(invoice_number: str, customer_phone: str, 
                                        owner_id: str) -> dict:
    """Generate and send invoice PDF to customer via WhatsApp"""
    try:
        # Find invoice
        invoices = get_all_invoices(owner_id=owner_id)
        invoice = None
        for inv in invoices:
            if inv['invoice_number'] == invoice_number:
                invoice = inv
                break
        
        if not invoice:
            return {"error": f"Invoice {invoice_number} not found"}
        
        # Get invoice items
        from database import get_invoice_items
        items = get_invoice_items(invoice['id'])
        invoice['items'] = items
        
        # Get business owner info for invoice header
        from database import get_business_owner
        owner = get_business_owner(owner_id)
        
        business_info = {
            'name': owner.get('business_name', 'Your Business') if owner else 'Your Business',
            'address': owner.get('business_address', '') if owner else '',
            'phone': owner_id,
            'gstin': owner.get('business_gstin', '') if owner else '',
        }
        
        # Generate PDF
        from pdf_generator import generate_invoice_pdf
        pdf_path = generate_invoice_pdf(invoice, business_info=business_info)
        
        # Send via WhatsApp
        from app import send_invoice_pdf_to_customer
        await send_invoice_pdf_to_customer(
            customer_phone=customer_phone,
            pdf_path=pdf_path,
            invoice_number=invoice_number,
            owner_id=owner_id
        )
        
        return {
            "success": True,
            "message": f"Invoice {invoice_number} sent to {customer_phone}",
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        logger.error(f"Send invoice error: {e}", exc_info=True)
        return {"error": str(e)}


def _get_product_info(product_name: Optional[str], owner_id: str) -> list:
    """Return matching products with price/stock info."""
    all_products = get_all_products(owner_id)
    if not product_name:
        return all_products
    needle = product_name.lower()
    matches = [p for p in all_products if needle in p['name'].lower()]
    return matches if matches else all_products  # fallback to all if no match


def _get_sales_history(product_name: Optional[str], customer_name: Optional[str], owner_id: str) -> dict:
    """Return recent invoices filtered by product or customer."""
    invoices = get_all_invoices(owner_id)
    # Get items for each invoice so we can filter by product
    from database import get_invoice_items
    result = []
    for inv in invoices:
        try:
            items = get_invoice_items(inv['id'])
        except Exception:
            items = []
        inv['items'] = items
        # Filter by product name if specified
        if product_name:
            needle = product_name.lower()
            if not any(needle in (it.get('product_name','') or '').lower() for it in items):
                continue
        # Filter by customer name if specified
        if customer_name:
            if customer_name.lower() not in (inv.get('customer_name','') or '').lower():
                continue
        result.append(inv)
    return {
        "total_invoices": len(result),
        "invoices": result[:20]  # cap at 20 to avoid token overflow
    }


def _execute_function(fn: str, args: Dict[str, Any]) -> Any:
    oid = args.pop('owner_id', 'default')
    
    # Special handling for async functions
    if fn == "send_invoice_to_customer":
        import asyncio
        return asyncio.run(send_invoice_to_customer_impl(
            invoice_number=args.get("invoice_number"),
            customer_phone=args.get("customer_phone"),
            owner_id=oid
        ))
    
    dispatch = {
        "create_invoice":        lambda: create_invoice(owner_id=oid, **args),
        "record_payment":        lambda: record_payment(owner_id=oid, **args),
        "update_inventory":      lambda: update_inventory(owner_id=oid, **args),
        "create_product":        lambda: create_product(owner_id=oid, **args),
        "create_customer":       lambda: create_customer(owner_id=oid, **args),
        "get_daily_summary":     lambda: get_daily_summary(owner_id=oid),
        "get_customer_details":  lambda: get_customer_by_name(args.get("customer_name"), oid),
        "get_overdue_reminders": lambda: get_overdue_customers(args.get("days", 14), oid),
        "get_low_stock_alert":   lambda: get_low_stock_products(oid),
        "get_product_info":      lambda: _get_product_info(args.get("product_name"), oid),
        "get_sales_history":     lambda: _get_sales_history(
            args.get("product_name"), args.get("customer_name"), oid),
        "get_warranty_info":     lambda: get_warranty_info(
            product_name=args.get("product_name"),
            customer_name=args.get("customer_name"),
            owner_id=oid
        ),
    }
    fn_callable = dispatch.get(fn)
    if not fn_callable:
        return {"error": f"Unknown function: {fn}"}
    try:
        return fn_callable()
    except Exception as e:
        logger.error(f"Function {fn} failed: {e}")
        return {"error": str(e)}
