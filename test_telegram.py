# test_telegram.py
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("="*50)
print("🔍 Telegram Configuration Check")
print("="*50)

print(f"\nBot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
print(f"Chat ID: {TELEGRAM_CHAT_ID}")

# Test 1: Check if bot token is valid
print("\n📡 Testing bot token...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get('ok'):
        bot_info = data['result']
        print(f"✅ Bot found: @{bot_info['username']}")
        print(f"   Name: {bot_info['first_name']}")
    else:
        print(f"❌ Bot token invalid: {data}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Send a test message
print("\n📤 Testing message send...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': '🧪 Test message from SentinelCore'
    }
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()

    if data.get('ok'):
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Failed: {data.get('description', 'Unknown error')}")
        print("\n💡 Try these fixes:")
        print("   1. Make sure you've sent /start to your bot")
        print("   2. Get your correct Chat ID from @userinfobot")
        print("   3. Verify your bot token from @BotFather")
except Exception as e:
    print(f"❌ Error: {e}")
