import chat_ui
import dashboard
print("chat_ui router routes:", [r.path for r in chat_ui.router.routes])
print("dashboard router routes:", [r.path for r in dashboard.router.routes])
print("Imports OK")
