# telegram_alert.py
# ============================================================
# TELEGRAM ALERT SYSTEM
# Sends real-time notifications when anomalies are detected
# ============================================================

from datetime import datetime, timezone

import requests

from config import (
    ALERT_SEVERITY_LEVELS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
)


class TelegramAlert:
    """Send alerts to Telegram when suspicious transactions are detected"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.enabled = TELEGRAM_ENABLED and self.bot_token != "YOUR_BOT_TOKEN_HERE"
        self.severity_levels = ALERT_SEVERITY_LEVELS

        if self.enabled:
            print("✅ Telegram alerts enabled")
        else:
            print("⚠️ Telegram alerts disabled (check config)")

    def send_alert(self, alert_data):
        """
        Send an alert to Telegram

        Args:
            alert_data: Dictionary with alert information
        """
        if not self.enabled:
            return False

        # Check if severity is in allowed levels
        severity = alert_data.get('severity', 'LOW')
        if severity not in self.severity_levels:
            return False

        # Format the message
        message = self._format_alert_message(alert_data)

        # Send the message
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                print(
                    f"✅ Alert sent to Telegram: {alert_data.get('type', 'Unknown')}")
                return True
            else:
                print(f"❌ Failed to send Telegram alert: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    def _format_alert_message(self, alert_data):
        """Format alert data into a readable Telegram message"""
        timestamp = alert_data.get(
            'timestamp', datetime.now(timezone.utc).isoformat())
        alert_type = alert_data.get('type', 'UNKNOWN')
        severity = alert_data.get('severity', 'LOW')
        details = alert_data.get('details', 'No details provided')
        tx_data = alert_data.get('transaction', {})

        # Emoji based on severity
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
            'INFO': 'ℹ️'
        }.get(severity, '⚪')

        # Format the message
        message = f"""
{severity_emoji} <b>ALERT: {alert_type}</b>
🔗 <b>Chain:</b> {tx_data.get('chain_name', 'Unknown')}
📊 <b>Severity:</b> {severity}
🕐 <b>Time:</b> {timestamp}

📝 <b>Details:</b> {details}

📦 <b>Transaction:</b>
   • <b>Hash:</b> <code>{tx_data.get('hash', 'N/A')[:20]}...</code>
   • <b>From:</b> <code>{tx_data.get('from', 'N/A')[:20]}...</code>
   • <b>To:</b> <code>{tx_data.get('to', 'N/A')[:20]}...</code>
   • <b>Value:</b> {tx_data.get('value_eth', 0):.6f} {tx_data.get('native_symbol', '')}
   • <b>Block:</b> {tx_data.get('block', 'N/A')}

🔍 <i>Investigate immediately!</i>
        """
        return message.strip()

    def send_test_alert(self):
        """Send a test alert to verify Telegram integration"""
        test_alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'TEST_ALERT',
            'severity': 'INFO',
            'details': 'This is a test alert from SentinelCore - Telegram integration is working! ✅',
            'transaction': {
                'hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD68',
                'to': '0xabcdef1234567890abcdef1234567890abcdef12',
                'value_eth': 150.0,
                'block': 25939589
            }
        }
        return self.send_alert(test_alert)


# Quick test
if __name__ == "__main__":
    alert = TelegramAlert()
    alert.send_test_alert()
    print("✅ Test alert sent! Check your Telegram.")
