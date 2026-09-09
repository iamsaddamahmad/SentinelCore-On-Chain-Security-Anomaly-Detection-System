import os
from datetime import datetime
from config import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)

log_entry = f"{datetime.now().isoformat()} | SYSTEM | Test log entry - System is working\n"

with open(os.path.join(LOGS_DIR, 'alerts.log'), 'a') as f:
    f.write(log_entry)

print(f"✅ Test log created in: {LOGS_DIR}/alerts.log")
print("📝 Log entry:", log_entry.strip())
