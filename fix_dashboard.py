import re

with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all @app. route decorators with @router.
content = content.replace('@app.get(', '@router.get(')
content = content.replace('@app.post(', '@router.post(')
content = content.replace('@app.put(', '@router.put(')
content = content.replace('@app.delete(', '@router.delete(')

# Fix send_whatsapp_message calls to use lazy import
content = content.replace(
    'await send_whatsapp_message(',
    'await _send_whatsapp_message()('
)

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
