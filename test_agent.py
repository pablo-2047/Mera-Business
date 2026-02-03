"""
Test Script for Bharat Biz-Agent
Simulates WhatsApp messages for local testing without actual WhatsApp setup
"""

import asyncio
import sys
from intent_router import route_intent_and_execute
from database import init_database, get_daily_summary

# Test cases covering different scenarios
TEST_CASES = [
    # Invoice creation
    {
        "name": "Simple Sale",
        "input": "Ramesh ko Vivo V29 becha 29999 mein",
        "expected": "invoice created"
    },
    {
        "name": "Credit Sale (Udhaar)",
        "input": "Suresh ko Samsung S23 udhaar mein diya 54999 ka",
        "expected": "invoice created"
    },
    {
        "name": "Multi-item Sale",
        "input": "Amit ko 2 Vivo phones aur 1 iPhone becha total 1 lakh mein",
        "expected": "invoice created"
    },
    
    # Payment recording
    {
        "name": "UPI Payment",
        "input": "Ramesh se 5000 payment aaya UPI se",
        "expected": "payment recorded"
    },
    {
        "name": "Cash Payment",
        "input": "Suresh ne cash mein 10000 diye",
        "expected": "payment recorded"
    },
    
    # Inventory management
    {
        "name": "Add Stock",
        "input": "iPhone 15 ka stock 10 pieces add karo",
        "expected": "inventory updated"
    },
    {
        "name": "Check Low Stock",
        "input": "Kaun se products ka stock kam hai?",
        "expected": "low stock"
    },
    
    # Reporting
    {
        "name": "Daily Summary",
        "input": "Aaj ka hisaab batao",
        "expected": "summary"
    },
    {
        "name": "Pending Payments",
        "input": "Kisne abhi tak payment nahi kiya?",
        "expected": "overdue"
    },
    {
        "name": "Customer Balance",
        "input": "Ramesh ka kitna baaki hai?",
        "expected": "balance"
    },
    
    # Customer management
    {
        "name": "Add Customer",
        "input": "Naya customer add karo - Rakesh Singh, phone 9876543210",
        "expected": "customer"
    },
    
    # Mixed language queries
    {
        "name": "Hinglish Query",
        "input": "Kal payment bhej dena Suresh ko reminder",
        "expected": "reminder"
    },
    {
        "name": "English Query",
        "input": "Show me today's sales report",
        "expected": "sales"
    },
]


async def run_test(test_case):
    """Run a single test case"""
    print(f"\n{'='*80}")
    print(f"Test: {test_case['name']}")
    print(f"{'='*80}")
    print(f"Input: {test_case['input']}")
    print(f"\nProcessing...\n")
    
    try:
        response = await route_intent_and_execute(test_case['input'])
        print(f"Response:\n{response}")
        print(f"\n✅ Test completed")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    await asyncio.sleep(1)  # Avoid rate limiting


async def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*80)
    print("BHARAT BIZ-AGENT - TEST SUITE")
    print("="*80)
    print(f"Total Tests: {len(TEST_CASES)}")
    print("="*80)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}]", end=" ")
        await run_test(test_case)
        
        # Wait for user input between tests (optional)
        if i < len(TEST_CASES):
            user_input = input("\n\nPress Enter for next test (or 'q' to quit): ")
            if user_input.lower() == 'q':
                break
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)


async def interactive_mode():
    """Interactive testing mode"""
    print("\n" + "="*80)
    print("BHARAT BIZ-AGENT - INTERACTIVE MODE")
    print("="*80)
    print("Type your queries (or 'quit' to exit)")
    print("="*80 + "\n")
    
    while True:
        try:
            query = input("You: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            print("\nAgent: Processing...\n")
            response = await route_intent_and_execute(query)
            print(f"Agent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


async def quick_demo():
    """Quick demo with 3 essential operations"""
    print("\n" + "="*80)
    print("QUICK DEMO - 3 Essential Operations")
    print("="*80 + "\n")
    
    demos = [
        {
            "title": "1. Create Invoice (Sale)",
            "query": "Ramesh ko Vivo V29 becha 29999 mein"
        },
        {
            "title": "2. Record Payment",
            "query": "Ramesh se 5000 payment aaya UPI se"
        },
        {
            "title": "3. Daily Summary",
            "query": "Aaj ka hisaab batao"
        }
    ]
    
    for demo in demos:
        print(f"\n{demo['title']}")
        print("-" * 60)
        print(f"Query: {demo['query']}")
        print()
        
        response = await route_intent_and_execute(demo['query'])
        print(f"Response:\n{response}\n")
        
        await asyncio.sleep(2)
    
    print("=" * 80)
    print("Demo completed! 🎉")
    print("=" * 80)


def check_database():
    """Check database status"""
    print("\n" + "="*80)
    print("DATABASE STATUS CHECK")
    print("="*80 + "\n")
    
    try:
        summary = get_daily_summary()
        print("✅ Database is accessible")
        print(f"\nCurrent Summary:")
        print(f"  Sales: {summary['sales']['count']} invoices - ₹{summary['sales']['total']:,.2f}")
        print(f"  Payments: {summary['payments']['count']} received - ₹{summary['payments']['total']:,.2f}")
        print(f"  Outstanding: ₹{summary['outstanding_udhaar']:,.2f}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        print("\nTrying to initialize database...")
        try:
            init_database()
            print("✅ Database initialized successfully")
        except Exception as init_error:
            print(f"❌ Failed to initialize: {str(init_error)}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        # Show menu
        print("\n" + "="*80)
        print("BHARAT BIZ-AGENT - TEST RUNNER")
        print("="*80)
        print("\nSelect mode:")
        print("  1. Quick Demo (3 operations)")
        print("  2. Full Test Suite")
        print("  3. Interactive Mode")
        print("  4. Check Database")
        print("  5. Exit")
        print("="*80)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            mode = 'demo'
        elif choice == '2':
            mode = 'test'
        elif choice == '3':
            mode = 'interactive'
        elif choice == '4':
            mode = 'check'
        else:
            print("Exiting...")
            return
    
    # Execute selected mode
    if mode == 'demo':
        asyncio.run(quick_demo())
    elif mode == 'test':
        asyncio.run(run_all_tests())
    elif mode == 'interactive':
        asyncio.run(interactive_mode())
    elif mode == 'check':
        check_database()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python test_agent.py [demo|test|interactive|check]")


if __name__ == "__main__":
    main()
