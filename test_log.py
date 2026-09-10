import os
from datetime import datetime, timezone

from config import LOGS_DIR


def test_log_creation():
    os.makedirs(LOGS_DIR, exist_ok=True)

    log_entry = f"{datetime.now(timezone.utc).isoformat()} | SYSTEM | Test log entry - System is working\n"
    log_path = os.path.join(LOGS_DIR, 'alerts.log')

    with open(log_path, 'a') as f:
        f.write(log_entry)

    # Actual assertions — verifies the log file exists and the entry landed
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        contents = f.read()
    assert log_entry.strip() in contents
    assert 'SYSTEM' in contents
