"""
Bharat Biz-Agent - Intent Router with Gemini
Implements agentic AI with function calling for business operations
"""

import os
import base64
import json
import logging
from typing import Optional, List, Dict, Any, Callable
import google.generativeai as genai

from database import (
    create_product, update_inventory, get_low_stock_products,
    create_customer, get_customer_by_name,
    create_invoice, record_payment,
    get_daily_summary, get_overdue_customers
)

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ==================== System Prompt ====================

SYSTEM_INSTRUCTION = """तुम एक intelligent business assistant हो जो Indian SMB owners की मदद करता है। 

तुम्हारी ज़िम्मेदारियाँ:
1. Users के messages को समझना (Hindi, English, Hinglish में)
2. Business operations execute करना (invoices, inventory, payments)
3. Natural और helpful responses देना

Key Guidelines:
- User की language में respond करो (agar Hindi/Hinglish bola to ussi mein reply karo)
- Business context समझो (GST, UPI, credit/udhaar)
- Confirm करो sensitive actions के लिए
- Numbers को clearly format करो (₹2,000 ऐसे)
- Dates को Indian format में बताओ (DD/MM/YYYY)

Business Terms को समझो:
- "बेचा"/"sold" = create invoice
- "उधार"/"credit" = invoice without immediate payment  
- "payment आया"/"received" = record payment
- "stock कम है" = low inventory alert
- "हिसाब"/"ledger" = check accounts/summary

Examples:
User: "Ramesh ko Vivo V29 becha 29999 mein"
→ create_invoice(customer="Ramesh", items=[{"product":"Vivo V29", "quantity":1, "rate":29999}])

User: "Suresh se 5000 payment aaya UPI se"  
→ record_payment(customer="Suresh", amount=5000, payment_mode="UPI")

User: "Aaj ka hisaab batao"
→ get_daily_summary()

User: "iPhone 15 ka stock 5 pieces add karo"
→ update_inventory(product="iPhone 15", quantity=5, operation="add")

Always be helpful, accurate, and culturally aware!
"""


# ==================== Function Definitions for Gemini ====================

def get_function_declarations() -> List[Dict[str, Any]]:
    """
    Define all available functions for Gemini's function calling
    
    These are the "tools" that Gemini can use to execute actual business operations
    """
    return [
        {
            "name": "create_invoice",
            "description": """Create a sales invoice for a customer. Use this when customer buys products.
            Supports both cash sales and credit (udhaar). Automatically updates inventory.
            Examples: 'Ramesh ko phone becha', 'invoice create karo', 'bill banao'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer"
                    },
                    "items": {
                        "type": "array",
                        "description": "List of products sold",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string", "description": "Product name"},
                                "quantity": {"type": "number", "description": "Quantity sold"},
                                "rate": {"type": "number", "description": "Price per unit"},
                                "gst_rate": {"type": "number", "description": "GST percentage (default 18)"}
                            },
                            "required": ["product_name", "quantity", "rate"]
                        }
                    },
                    "payment_mode": {
                        "type": "string",
                        "description": "Payment method: UPI, Cash, Card, or null for credit",
                        "enum": ["UPI", "Cash", "Card", None]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes (optional)"
                    }
                },
                "required": ["customer_name", "items"]
            }
        },
        {
            "name": "record_payment",
            "description": """Record a payment received from customer. Use when customer pays money.
            Examples: 'payment aaya', 'paisa mila', 'amount received'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer who paid"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Payment amount in rupees"
                    },
                    "payment_mode": {
                        "type": "string",
                        "description": "Payment method",
                        "enum": ["UPI", "Cash", "Card", "Bank Transfer"],
                        "default": "UPI"
                    },
                    "utr_number": {
                        "type": "string",
                        "description": "UTR/transaction reference number (optional)"
                    }
                },
                "required": ["customer_name", "amount"]
            }
        },
        {
            "name": "update_inventory",
            "description": """Update product inventory/stock. Use to add or reduce stock.
            Examples: 'stock add karo', 'inventory update', 'stock kam karo'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add or reduce"
                    },
                    "operation": {
                        "type": "string",
                        "description": "Operation type",
                        "enum": ["add", "reduce"],
                        "default": "add"
                    }
                },
                "required": ["product_name", "quantity"]
            }
        },
        {
            "name": "create_product",
            "description": """Add a new product to inventory. Use when adding new product for the first time.
            Examples: 'naya product add karo', 'new item daalo'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Product name"
                    },
                    "stock": {
                        "type": "integer",
                        "description": "Initial stock quantity",
                        "default": 0
                    },
                    "cost_price": {
                        "type": "number",
                        "description": "Purchase/cost price",
                        "default": 0
                    },
                    "selling_price": {
                        "type": "number",
                        "description": "Selling price",
                        "default": 0
                    },
                    "gst_rate": {
                        "type": "number",
                        "description": "GST rate (5, 12, 18, or 28)",
                        "enum": [5, 12, 18, 28],
                        "default": 18
                    }
                },
                "required": ["name", "selling_price"]
            }
        },
        {
            "name": "create_customer",
            "description": """Add or update customer details. Use when adding new customer.
            Examples: 'naya customer add karo', 'customer details save karo'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Customer name"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address (optional)"
                    },
                    "address": {
                        "type": "string",
                        "description": "Customer address (optional)"
                    }
                },
                "required": ["name", "phone"]
            }
        },
        {
            "name": "get_daily_summary",
            "description": """Get today's business summary - sales, payments, expenses.
            Examples: 'aaj ka hisaab', 'today's summary', 'aaj kitna hua'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (default: today)"
                    }
                }
            }
        },
        {
            "name": "get_customer_details",
            "description": """Get customer details and outstanding balance.
            Examples: 'Ramesh ka balance batao', 'customer ka hisaab'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer"
                    }
                },
                "required": ["customer_name"]
            }
        },
        {
            "name": "get_overdue_reminders",
            "description": """Get list of customers with overdue payments who need reminders.
            Examples: 'pending payments', 'kaun baaki hai', 'reminder bhejne hain'""",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days overdue (default: 30)",
                        "default": 30
                    }
                }
            }
        },
        {
            "name": "get_low_stock_alert",
            "description": """Get products that are running low on stock.
            Examples: 'stock kam hai kiske paas', 'low stock alert', 'inventory check karo'""",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]


# ==================== Function Execution Map ====================

def get_customer_details(customer_name: str) -> Dict[str, Any]:
    """Wrapper to get customer details"""
    customer = get_customer_by_name(customer_name)
    if not customer:
        return {"error": f"Customer '{customer_name}' not found"}
    return customer


def get_overdue_reminders(days: int = 30) -> List[Dict[str, Any]]:
    """Wrapper for overdue customers"""
    return get_overdue_customers(days)


def get_low_stock_alert() -> List[Dict[str, Any]]:
    """Wrapper for low stock products"""
    return get_low_stock_products()


# Map function names to actual Python functions
FUNCTION_MAP: Dict[str, Callable] = {
    "create_invoice": create_invoice,
    "record_payment": record_payment,
    "update_inventory": update_inventory,
    "create_product": create_product,
    "create_customer": create_customer,
    "get_daily_summary": get_daily_summary,
    "get_customer_details": get_customer_details,
    "get_overdue_reminders": get_overdue_reminders,
    "get_low_stock_alert": get_low_stock_alert,
}


# ==================== Main Intent Router ====================

async def route_intent_and_execute(
    text_content: str,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None
) -> str:
    """
    Main intent routing function using Gemini with function calling
    
    Flow:
    1. Prepare multimodal input (text + optional image/audio)
    2. Send to Gemini with function declarations
    3. If Gemini returns function call → execute it
    4. Send result back to Gemini for natural response
    5. Return final response to user
    
    Args:
        text_content: User's text message
        media_path: Path to audio/image file (optional)
        media_type: Type of media (audio/image)
        
    Returns:
        Response message for user
    """
    try:
        # Initialize model with function calling
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[{"function_declarations": get_function_declarations()}]
        )
        
        # Prepare content for Gemini
        content_parts = []
        
        # Add media if present
        if media_path and media_type:
            if media_type == "audio":
                # For audio, we need to transcribe first or send as audio
                with open(media_path, "rb") as f:
                    audio_data = base64.b64encode(f.read()).decode()
                content_parts.append({
                    "mime_type": "audio/ogg",
                    "data": audio_data
                })
            elif media_type == "image":
                # For images, Gemini can analyze directly
                with open(media_path, "rb") as f:
                    image_data = f.read()
                content_parts.append({
                    "mime_type": "image/jpeg",
                    "data": image_data
                })
        
        # Add text content
        if text_content:
            content_parts.append(text_content)
        elif not content_parts:
            return "मुझे समझ नहीं आया। कृपया फिर से बताएं।"
        
        # Start chat
        chat = model.start_chat(enable_automatic_function_calling=False)
        
        # Send message to Gemini
        response = chat.send_message(content_parts)
        
        # Check if Gemini wants to call a function
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            function_name = function_call.name
            function_args = dict(function_call.args)
            
            logger.info(f"Gemini called function: {function_name} with args: {function_args}")
            
            # Execute the function
            if function_name in FUNCTION_MAP:
                try:
                    result = FUNCTION_MAP[function_name](**function_args)
                    
                    # Send result back to Gemini for natural response
                    function_response = chat.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result}
                                )
                            )]
                        )
                    )
                    
                    return function_response.text
                    
                except Exception as e:
                    logger.error(f"Error executing function {function_name}: {str(e)}", exc_info=True)
                    return f"Error: {str(e)}"
            else:
                return f"Function {function_name} not found in system"
        
        # No function call, return direct response
        return response.text
        
    except Exception as e:
        logger.error(f"Error in intent routing: {str(e)}", exc_info=True)
        return f"क्षमा करें, कुछ गड़बड़ हो गई: {str(e)}"


# ==================== Helper Functions ====================

def format_amount(amount: float) -> str:
    """Format amount in Indian rupee style"""
    return f"₹{amount:,.2f}"


def format_date(date_str: str) -> str:
    """Convert date to DD/MM/YYYY format"""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y")
    except:
        return date_str


# ==================== Testing ====================

if __name__ == "__main__":
    import asyncio
    
    async def test_intent_router():
        """Test the intent router with sample queries"""
        
        test_cases = [
            "Ramesh ko Vivo V29 becha 29999 mein",
            "Suresh se 5000 payment aaya UPI se",
            "Aaj ka hisaab batao",
            "iPhone 15 ka stock 5 pieces add karo",
            "Kaun kaun ka payment pending hai?",
        ]
        
        print("Testing Intent Router...\n")
        
        for query in test_cases:
            print(f"Query: {query}")
            response = await route_intent_and_execute(query)
            print(f"Response: {response}\n")
            print("-" * 80)
    
    # Run tests
    # asyncio.run(test_intent_router())
    print("Intent router module loaded. Import and use route_intent_and_execute() function.")
