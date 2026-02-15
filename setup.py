"""
Mera Business — One-Click Setup Script
Automates: venv creation, dependency installation, database init, sample data
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run shell command and handle errors"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"  ✅ {description} — Done!")
        return result
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr}")
        return None

def main():
    print_header("🏪 Mera Business — Setup Script")
    print("This will:")
    print("  1. Create Python virtual environment")
    print("  2. Install all dependencies")
    print("  3. Initialize database with schema")
    print("  4. Add sample products & customers")
    print("  5. Create .env file from template")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Detect OS
    is_windows = platform.system() == "Windows"
    python_cmd = "python" if is_windows else "python3"
    pip_cmd = "pip" if is_windows else "pip3"
    
    # Step 1: Create virtual environment
    print_header("Step 1: Creating Virtual Environment")
    venv_path = Path("venv")
    if venv_path.exists():
        print("  ⚠️  venv already exists — skipping creation")
    else:
        run_command(f"{python_cmd} -m venv venv", "Creating venv")
    
    # Determine activation script path
    if is_windows:
        activate_script = r"venv\Scripts\activate"
        pip_executable = r"venv\Scripts\pip.exe"
        python_executable = r"venv\Scripts\python.exe"
    else:
        activate_script = "venv/bin/activate"
        pip_executable = "venv/bin/pip"
        python_executable = "venv/bin/python"
    
    print(f"\n  💡 Activate venv manually:\n     {activate_script}\n")
    
    # Step 2: Install dependencies
    print_header("Step 2: Installing Dependencies")
    
    # Upgrade pip first
    run_command(f"{pip_executable} install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        run_command(
            f"{pip_executable} install -r requirements.txt", 
            "Installing packages from requirements.txt"
        )
    else:
        print("  ❌ requirements.txt not found!")
        sys.exit(1)
    
    # Step 3: Initialize database
    print_header("Step 3: Initializing Database")
    run_command(
        f"{python_executable} -c \"from database import init_database; init_database()\"",
        "Creating database tables"
    )
    
    # Step 4: Add sample data
    print_header("Step 4: Adding Sample Data")
    run_command(f"{python_executable} _test.py", "Running test script")
    
    # Step 5: Create .env file
    print_header("Step 5: Environment Configuration")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("  ⚠️  .env already exists — skipping")
    elif env_example_path.exists():
        import shutil
        shutil.copy(env_example_path, env_path)
        print("  ✅ Created .env from .env.example")
        print("\n  ⚠️  IMPORTANT: Edit .env and add your API keys!")
        print("     Required keys:")
        print("       - GEMINI_API_KEY")
        print("       - WHATSAPP_TOKEN")
        print("       - WHATSAPP_PHONE_NUMBER_ID")
    else:
        print("  ⚠️  .env.example not found — creating blank .env")
        with open(".env", "w") as f:
            f.write("""# Mera Business — Environment Variables

# WhatsApp Cloud API
WHATSAPP_VERIFY_TOKEN=mera_business_verify_token_12345
WHATSAPP_TOKEN=EAA_YOUR_TOKEN_HERE
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID

# Business Owner Phone (with country code)
BUSINESS_OWNER_PHONE=+91XXXXXXXXXX

# Authorized Test Phones (comma-separated)
AUTHORIZED_TEST_PHONES=+91XXXXXXXXXX,+91YYYYYYYYYY

# Google Gemini AI
GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE

# Business Details (for invoices)
BUSINESS_NAME=Your Shop Name
BUSINESS_ADDRESS=Your Shop Address, City, State
BUSINESS_PHONE=+91-XXXXXXXXXX
BUSINESS_EMAIL=yourshop@email.com
BUSINESS_GSTIN=GSTIN_NUMBER_HERE

# Optional: UPI for payment links
BUSINESS_UPI_ID=yourshop@paytm
""")
        print("  ✅ Created .env template")
    
    # Step 6: Test server
    print_header("Step 6: Testing Server")
    print("  Starting test server on http://localhost:8000")
    print("  Press Ctrl+C to stop\n")
    
    try:
        subprocess.run(
            f"{python_executable} -m uvicorn app:app --host 0.0.0.0 --port 8000",
            shell=True
        )
    except KeyboardInterrupt:
        print("\n\n  Server stopped.")
    
    # Final instructions
    print_header("✅ Setup Complete!")
    print("""
Next Steps:
    
1. Edit .env file with your API keys:
   - Get Gemini API key: https://aistudio.google.com/app/apikey
   - Get WhatsApp token: https://developers.facebook.com
    
2. Start the server:
   Windows: venv\\Scripts\\activate && uvicorn app:app --reload
   Mac/Linux: source venv/bin/activate && uvicorn app:app --reload
    
3. For public access (webhook testing):
   In another terminal: ngrok http 8000
    
4. Access dashboard: http://localhost:8000
    
5. Setup WhatsApp webhook:
   Dashboard → Configuration → Webhook URL
    
For detailed instructions, see: COMPLETE_SETUP_GUIDE.md
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
