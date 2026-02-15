# ⚡ QUICK FIX - Database Locked Error

## 🔧 Problem
```
sqlite3.OperationalError: database is locked
```

## ✅ Solution (Choose One):

### Option 1: Use the Fix Script (EASIEST)
```bash
python fix_and_regenerate.py
```
**This automatically:**
- Closes all Python processes
- Deletes database files
- Regenerates sample data

### Option 2: Manual Steps
```powershell
# 1. Close all Python
Get-Process python | Stop-Process -Force

# 2. Delete database
del bharat_biz.db
del bharat_biz.db-shm
del bharat_biz.db-wal

# 3. Regenerate
python generate_sample_data.py
```

### Option 3: Just Close Processes
```powershell
# If database is new, just close processes
Get-Process python | Stop-Process -Force

# Wait 2 seconds, then:
python generate_sample_data.py
```

## ✅ After Fix:
```bash
# Start server
python app.py

# Open browser
http://localhost:8000/chat
```

## 🎯 What's Fixed:
- Added delays between database operations
- Better error handling
- Automatic WAL checkpoint
- Graceful failure handling

## ✅ You're Ready!
The script should work now without database locks!
