
# test_alert.py - Generate a test alert
import json
import os
from datetime import datetime
from config import ALERTS_DIR

# Create alerts directory if it doesn't exist
os.makedirs(ALERTS_DIR, exist_ok=True)

# Create a test alert
test_alert = {
    'timestamp': datetime.now().isoformat(),
    'alert': {
        'type': 'TEST_ALERT',
        'severity': 'HIGH',
        'details': 'This is a test alert to verify the system is working'
    },
    'transaction': {
        'hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD68',
        'to': '0xabcdef1234567890abcdef1234567890abcdef12',
        'value_eth': 150.0,
        'block': 25939589
    }
}

# Save to alerts file
filename = f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
filepath = os.path.join(ALERTS_DIR, filename)

# Load existing alerts or create new list
try:
    with open(filepath, 'r') as f:
        alerts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    alerts = []

alerts.append(test_alert)

with open(filepath, 'w') as f:
    json.dump(alerts, f, indent=2)

print(f"✅ Test alert created in: {filepath}")
print(f"📊 Total alerts in file: {len(alerts)}")
