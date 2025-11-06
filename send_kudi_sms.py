"""
Church Bulk SMS Automation - KudiSMS Version
Author: Peace Mathew

This script sends SMS messages to multiple recipients
via KudiSMS API using credentials from environment variables.
"""

import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables (works in local + GitHub Actions)
load_dotenv()

# 🔐 Credentials (from .env or GitHub Secrets)
KUDI_USERNAME = os.getenv("KUDI_USERNAME")
KUDI_API_KEY  = os.getenv("KUDI_API_KEY")
SENDER_ID     = os.getenv("SENDER_ID", "ChurchBot")
RECIPIENTS    = os.getenv("RECIPIENTS", "")
MESSAGE       = os.getenv("MESSAGE", "Hello! Reminder: Please attend church service tomorrow.")

# ✅ Correct API endpoint
API_URL = "https://account.kudisms.net/api/?action=send-sms"

# ✅ Validate required inputs
if not KUDI_USERNAME or not KUDI_API_KEY:
    print("\n❌ ERROR: Missing KUDI_USERNAME or KUDI_API_KEY.\n")
    exit(1)

# Convert CSV numbers into list
recipients_list = [num.strip() for num in RECIPIENTS.split(",") if num.strip()]

# Header / log formatting
print("\n============================================================")
print("✅ KudiSMS BULK SENDER")
print("============================================================\n")
print(f"📱 Recipients Count: {len(recipients_list)}")
print(f"📤 Sender ID:        {SENDER_ID}")
print(f"💬 Message:          {MESSAGE}")
print(f"🔗 API Endpoint:     {API_URL}")
print("============================================================")
print("🚀 Starting SMS sending...\n")

success, failed = 0, 0

# Loop through numbers and send SMS
for index, number in enumerate(recipients_list, start=1):

    print(f"[{index}/{len(recipients_list)}] ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) Sending to {number}...")

    payload = {
        "username": KUDI_USERNAME,
        "password": KUDI_API_KEY,
        "recipient": number,
        "sender": SENDER_ID,
        "message": MESSAGE,
    }

    try:
        response = requests.post(API_URL, data=payload, timeout=15)
        resp_text = response.text.strip()

        if resp_text.upper().startswith("OK"):
            print(f" ✅ SUCCESS → {resp_text}")
            success += 1
        else:
            print(f" ❌ FAILED → {resp_text}")
            failed += 1

    except Exception as e:
        print(f" ⚠️ ERROR: {e}")
        failed += 1

    time.sleep(0.6)  # avoid rate limit

# Final summary output
print("\n============================================================")
print("📊 DELIVERY REPORT")
print("============================================================")
print(f"✅ Successful: {success}")
print(f"❌ Failed:     {failed}")
print(f"📱 Total:      {len(recipients_list)}")
print("============================================================\n")
