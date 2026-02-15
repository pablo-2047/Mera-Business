"""
Quick Fix Script - Closes processes and regenerates database
Run this if you get "database is locked" errors
"""

import subprocess
import os
import time

print("\n" + "="*60)
print("DATABASE LOCK FIX SCRIPT")
print("="*60)

print("\n[*] Closing all Python processes...")
try:
    # Close Python processes
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                   capture_output=True, text=True)
    subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], 
                   capture_output=True, text=True)
    print("[OK] Python processes closed")
except:
    print("[WARN] Could not close processes (might not be running)")

# Wait a moment
time.sleep(1)

print("\n[*] Removing old database files...")
try:
    if os.path.exists("bharat_biz.db"):
        os.remove("bharat_biz.db")
        print("[OK] Removed bharat_biz.db")
    if os.path.exists("bharat_biz.db-shm"):
        os.remove("bharat_biz.db-shm")
        print("[OK] Removed bharat_biz.db-shm")
    if os.path.exists("bharat_biz.db-wal"):
        os.remove("bharat_biz.db-wal")
        print("[OK] Removed bharat_biz.db-wal")
except Exception as e:
    print(f"[WARN] Could not remove some files: {e}")

print("\n[*] Regenerating sample data...")
time.sleep(1)

try:
    subprocess.run(["python", "generate_sample_data.py"], check=True)
except Exception as e:
    print(f"[ERROR] Failed to generate data: {e}")
    print("\n[*] Try running manually: python generate_sample_data.py")

print("\n" + "="*60)
print("DONE! Database should be ready now")
print("="*60)
print("\nNext: python app.py")
print("="*60 + "\n")
