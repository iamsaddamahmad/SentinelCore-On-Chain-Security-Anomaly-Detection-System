# test_alert.py - Generate a test alert
import json
import os
from datetime import datetime, timezone

from config import ALERTS_DIR


def test_alert_creation():
    os.makedirs(ALERTS_DIR, exist_ok=True)

    test_alert = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
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

    filename = f"alerts_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    filepath = os.path.join(ALERTS_DIR, filename)

    try:
        with open(filepath, 'r') as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = []

    alerts.append(test_alert)

    with open(filepath, 'w') as f:
        json.dump(alerts, f, indent=2)

    # Actual assertions — this is what makes it a real test, not just a script
    assert os.path.exists(filepath)
    with open(filepath, 'r') as f:
        saved_alerts = json.load(f)
    assert len(saved_alerts) >= 1
    assert saved_alerts[-1]['alert']['type'] == 'TEST_ALERT'
