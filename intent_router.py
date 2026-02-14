"""
Bharat Biz-Agent — Production Intent Router
Uses google-genai (latest) with Context Caching for 90% cost reduction
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from database import (
    create_invoice, record_payment, update_inventory,
    create_product, create_customer, get_daily_summary,
    get_customer_by_name, get_overdue_customers, get_low_stock_products
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = 'gemini-2.5-flash'
_cache_instance = None  # Module-level cache (lives for server lifetime)

SYSTEM_INSTRUCTION = """तुम एक intelligent business assistant हो जो Indian SMB owners की मदद करता है।

तुम्हारी ज़िम्मेदारियाँ:
1. Users के messages को समझना (Hindi, English, Hinglish में)
2. Business operations execute करना (invoices, inventory, payments)
3. Natural और helpful responses देना

Business Terms:
- "बेचा" / "sold" / "becha"     = create_invoice
- "उधार" / "udhaar" / "credit"  = create_invoice (no payment_mode)
- "payment आया" / "diya"        = record_payment
- "stock add" / "daalo"         = update_inventory (add)
- "हिसाब" / "summary"           = get_daily_summary
- "stock check"                 = get_low_stock_alert

Rules:
- Always respond in the user's language (Hindi if they use Hindi, etc.)
- Format amounts as ₹XX,XXX
- Dates as DD/MM/YYYY
- Be concise and friendly"""

TOOL_LIST = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="create_invoice",
            description="Create sales invoice. Use when customer buys something.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "customer_name": types.Schema(type=types.Type.STRING),
                    "items": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "product_name": types.Schema(type=types.Type.STRING),
                                "quantity": types.Schema(type=types.Type.NUMBER),
                                "rate": types.Schema(type=types.Type.NUMBER),
                                "gst_rate": types.Schema(type=types.Type.NUMBER),
                            },
                            required=["product_name", "quantity", "rate"]
                        )
                    ),
                    "payment_mode": types.Schema(type=types.Type.STRING, description="UPI/Cash/Card or omit for udhaar"),
                    "notes": types.Schema(type=types.Type.STRING),
                },
                required=["customer_name", "items"]
            )
        ),
        types.FunctionDeclaration(
            name="record_payment",
            description="Record payment received from customer",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "customer_name": types.Schema(type=types.Type.STRING),
                    "amount": types.Schema(type=types.Type.NUMBER),
                    "payment_mode": types.Schema(type=types.Type.STRING, description="UPI/Cash/Card"),
                    "utr_number": types.Schema(type=types.Type.STRING),
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
                    "quantity": types.Schema(type=types.Type.NUMBER),
                    "operation": types.Schema(type=types.Type.STRING, description="add or reduce"),
                },
                required=["product_name", "quantity"]
            )
        ),
        types.FunctionDeclaration(
            name="create_product",
            description="Add new product to inventory",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(type=types.Type.STRING),
                    "selling_price": types.Schema(type=types.Type.NUMBER),
                    "stock": types.Schema(type=types.Type.NUMBER),
                    "gst_rate": types.Schema(type=types.Type.NUMBER),
                    "cost_price": types.Schema(type=types.Type.NUMBER),
                },
                required=["name", "selling_price"]
            )
        ),
        types.FunctionDeclaration(
            name="get_daily_summary",
            description="Get today's sales, payments, expenses summary",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        ),
        types.FunctionDeclaration(
            name="get_customer_details",
            description="Get customer balance and transaction history",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"customer_name": types.Schema(type=types.Type.STRING)},
                required=["customer_name"]
            )
        ),
        types.FunctionDeclaration(
            name="get_overdue_reminders",
            description="Get list of customers with pending/overdue payments",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"days": types.Schema(type=types.Type.NUMBER)},
            )
        ),
        types.FunctionDeclaration(
            name="get_low_stock_alert",
            description="Get products running low on stock",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        ),
    ])
]


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=api_key)


def _get_or_create_cache(client: genai.Client):
    """
    Create or reuse Context Cache.
    Caches system_instruction + tools for 1 hour → 90% cost reduction.
    Falls back gracefully if caching not available.
    """
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    try:
        _cache_instance = client.caches.create(
            model=GEMINI_MODEL,
            config=types.CreateCachedContentConfig(
                display_name='mera_business_v1',
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOL_LIST,
                ttl=timedelta(hours=1),
            )
        )
        logger.info(f"Context Cache created: {_cache_instance.name}")
    except Exception as e:
        logger.warning(f"Context caching unavailable (need ≥2048 tokens): {e}")
        _cache_instance = "DISABLED"

    return _cache_instance


async def route_intent_and_execute(
    text_content: str,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None
) -> str:
    """
    Main entry point: text (+ optional media) → AI → function call → DB → response

    Args:
        text_content : User's message text
        media_path   : Local path to audio/image file (optional)
        media_type   : "audio" or "image"

    Returns:
        Natural language response string
    """
    if not text_content and not media_path:
        return "मुझे कुछ समझ नहीं आया। कृपया दोबारा बताएं।"

    client = _get_client()
    cache = _get_or_create_cache(client)

    # Build request config
    if cache != "DISABLED":
        req_config = types.GenerateContentConfig(
            cached_content=cache.name,
            temperature=0.7,
        )
    else:
        req_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=TOOL_LIST,
            temperature=0.7,
        )

    # Build content parts
    parts = []
    if media_path and media_type == "audio":
        import base64
        with open(media_path, "rb") as f:
            parts.append(types.Part(inline_data=types.Blob(
                mime_type="audio/ogg",
                data=base64.b64encode(f.read()).decode()
            )))
    if text_content:
        parts.append(types.Part(text=text_content))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Content(role="user", parts=parts)],
            config=req_config
        )

        candidate = response.candidates[0].content

        # Check every part for a function call
        for part in candidate.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_name = part.function_call.name
                func_args = dict(part.function_call.args) if part.function_call.args else {}
                logger.info(f"Function called: {func_name}({func_args})")

                result = _execute_function(func_name, func_args)

                # Round-trip: send result back for natural response
                followup_config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.5,
                )
                response2 = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[
                        types.Content(role="user", parts=[types.Part(text=text_content)]),
                        types.Content(role="model", parts=[part]),
                        types.Content(role="user", parts=[
                            types.Part(function_response=types.FunctionResponse(
                                name=func_name,
                                response={"result": str(result)}
                            ))
                        ]),
                    ],
                    config=followup_config
                )
                return response2.text

            elif hasattr(part, "text") and part.text:
                return part.text

        return "मुझे समझ नहीं आया। कृपया फिर से बताएं।"

    except Exception as e:
        logger.error(f"Intent routing error: {e}", exc_info=True)
        # Graceful fallback
        from simple_intent_router import route_intent_and_execute_simple
        return await route_intent_and_execute_simple(text_content)


def _execute_function(func_name: str, func_args: Dict[str, Any]) -> Any:
    """Dispatch function calls from Gemini to actual database functions"""
    dispatch = {
        "create_invoice":       lambda: create_invoice(**func_args),
        "record_payment":       lambda: record_payment(**func_args),
        "update_inventory":     lambda: update_inventory(**func_args),
        "create_product":       lambda: create_product(**func_args),
        "create_customer":      lambda: create_customer(**func_args),
        "get_daily_summary":    lambda: get_daily_summary(),
        "get_customer_details": lambda: get_customer_by_name(func_args.get("customer_name")),
        "get_overdue_reminders":lambda: get_overdue_customers(func_args.get("days", 30)),
        "get_low_stock_alert":  lambda: get_low_stock_products(),
    }
    fn = dispatch.get(func_name)
    if fn is None:
        return {"error": f"Unknown function: {func_name}"}
    try:
        return fn()
    except Exception as e:
        logger.error(f"Function {func_name} failed: {e}")
        return {"error": str(e)}
