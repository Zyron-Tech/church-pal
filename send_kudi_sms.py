import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ✅ Load credentials from .env
KUDI_USERNAME = os.getenv("KUDI_USERNAME")
KUDI_API_KEY = os.getenv("KUDI_API_KEY")
SENDER_ID = os.getenv("SENDER_ID", "PEACETECH")
RECIPIENTS = os.getenv("RECIPIENTS", "")
MESSAGE = os.getenv("MESSAGE", "Hello! This is a reminder from your church — we love you!")

# ✅ Correct API URL
API_URL = "https://kudisms.net/api/sendsms/"

# ✅ Check for missing env
if not KUDI_USERNAME or not KUDI_API_KEY:
    print("❌ ERROR: Missing KudiSMS username or API key.")
    exit(1)

recipients_list = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]

print("\n============================================================")
print("KudiSMS Bulk SMS Sender")
print("============================================================\n")
print(f"📱 Recipients: {len(recipients_list)} number(s)")
print(f"📤 Sender ID: {SENDER_ID}")
print(f"💬 Message: {MESSAGE[:45]}...")
print(f"🔗 API URL: {API_URL}")
print("\n============================================================")
print("Starting SMS delivery...\n")

success, failed = 0, 0

for index, number in enumerate(recipients_list, start=1):
    print(f"[{index}/{len(recipients_list)}] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sending to {number}...")

    payload = {
        "username": KUDI_USERNAME,
        "password": KUDI_API_KEY,
        "message": MESSAGE,
        "sender": SENDER_ID,
        "mobiles": number
    }

    try:
        response = requests.post(API_URL, data=payload)
        result = response.text

        if "OK" in result.upper():
            print(f"✅ Sent successfully ({number})")
            success += 1
        else:
            print("❌ Failed:", result)
            failed += 1

    except Exception as e:
        print("⚠️ Unexpected error:", e)
        failed += 1

    time.sleep(0.6)

print("\n============================================================")
print("📊 DELIVERY SUMMARY")
print("============================================================")
print(f"✅ Successful: {success}")
print(f"❌ Failed: {failed}")
print(f"📱 Total: {len(recipients_list)}")
print("============================================================")
