"""
🚀 ONE-COMMAND SETUP SCRIPT
Automates entire project setup for Neurathon judges

Usage: python setup_complete.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, desc):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {desc}")
    print('='*60)

def run_command(cmd, description):
    """Run shell command and handle errors"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return None

def check_python_version():
    """Ensure Python 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required!")
        print(f"Current version: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor} detected")

def create_venv():
    """Create virtual environment"""
    if os.path.exists("venv"):
        print("→ Virtual environment already exists, skipping...")
        return
    
    run_command("python -m venv venv", "Creating virtual environment")

def activate_venv():
    """Activate virtual environment"""
    if sys.platform == "win32":
        activate_script = "venv\\Scripts\\activate.bat"
        print(f"→ To activate later: {activate_script}")
    else:
        activate_script = "source venv/bin/activate"
        print(f"→ To activate later: {activate_script}")

def install_dependencies():
    """Install Python packages"""
    pip_cmd = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
    
    run_command(f"{pip_cmd} install --upgrade pip", 
                "Upgrading pip")
    
    run_command(f"{pip_cmd} install -r requirements.txt", 
                "Installing dependencies")

def create_env_file():
    """Create .env from .env.example"""
    if os.path.exists(".env"):
        print("→ .env already exists, skipping...")
        return
    
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✅ Created .env from .env.example")
        print("\n⚠️  IMPORTANT: Edit .env and add your API keys!")
        print("   Required:")
        print("   - WHATSAPP_TOKEN")
        print("   - WHATSAPP_PHONE_NUMBER_ID")
        print("   - GEMINI_API_KEY")
        print("   - BUSINESS_OWNER_PHONE")
    else:
        print("❌ .env.example not found!")

def init_database():
    """Initialize SQLite database"""
    python_cmd = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
    
    run_command(f'{python_cmd} -c "from database import init_database; init_database()"',
                "Initializing database")
    
    if os.path.exists("bharat_biz.db"):
        print("✅ Database created: bharat_biz.db")

def add_sample_data():
    """Add sample products and customers"""
    python_cmd = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
    
    run_command(f"{python_cmd} _test.py", 
                "Adding sample data")

def create_gitignore():
    """Create .gitignore if missing"""
    if os.path.exists(".gitignore"):
        return
    
    gitignore_content = """# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Environment
.env
*.db
*.sqlite

# Media
logs/
media/
temp/

# IDE
.vscode/
.idea/
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("✅ Created .gitignore")

def check_docker():
    """Check if Docker is installed"""
    result = run_command("docker --version", "Checking Docker")
    if result:
        print(f"   {result.strip()}")

def print_next_steps():
    """Print what to do next"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📝 NEXT STEPS:\n")
    
    print("1. Configure API Keys:")
    print("   → Edit .env file")
    print("   → Add WHATSAPP_TOKEN, GEMINI_API_KEY, etc.")
    
    print("\n2. Start the server:")
    if sys.platform == "win32":
        print("   → venv\\Scripts\\activate")
    else:
        print("   → source venv/bin/activate")
    print("   → uvicorn app:app --reload --port 8000")
    
    print("\n3. Test WhatsApp:")
    print("   → Open another terminal")
    print("   → ngrok http 8000")
    print("   → Copy ngrok URL to Meta Developer Console")
    
    print("\n4. Access Dashboard:")
    print("   → http://localhost:8000")
    
    print("\n5. Deploy to Production:")
    print("   → git push")
    print("   → Deploy on Railway/Render")
    
    print("\n📖 For detailed guides, see:")
    print("   - docs/MASTER_GUIDE.md")
    print("   - COMPLETE_SETUP_GUIDE.md")
    print("   - DEPLOYMENT.md")
    
    print("\n🏆 Good luck with Neurathon 2026!")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        🇮🇳 MERA BUSINESS - NEURATHON 2026 🇮🇳           ║
    ║                                                          ║
    ║          One-Command Setup for Hackathon                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        print_step(1, "Checking Python version")
        check_python_version()
        
        print_step(2, "Creating virtual environment")
        create_venv()
        
        print_step(3, "Installing dependencies")
        install_dependencies()
        
        print_step(4, "Creating .env file")
        create_env_file()
        
        print_step(5, "Creating .gitignore")
        create_gitignore()
        
        print_step(6, "Initializing database")
        init_database()
        
        print_step(7, "Adding sample data")
        add_sample_data()
        
        print_step(8, "Checking Docker (optional)")
        check_docker()
        
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
