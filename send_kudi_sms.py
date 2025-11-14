"""
Church Bulk SMS Automation - KudiSMS Version
Author: Peace Mathew
This script sends SMS messages to multiple recipients
via KudiSMS API using credentials from environment variables.
"""
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables (works in local + GitHub Actions)
load_dotenv()

# 🔐 Credentials (from .env or GitHub Secrets)
KUDI_API_KEY = os.getenv("KUDI_API_KEY", "zTLNJlOueo2nMsh19VRfyX7B4CZrxgwIUpac0DGHtvWFPA5dbK83SQmij6EkYq")  # This is your token
SENDER_ID = os.getenv("SENDER_ID", "ChurchBot")
RECIPIENTS = "2349032043408"
MESSAGE = os.getenv("MESSAGE", "Hello! ")
GATEWAY = os.getenv("GATEWAY", "2")

# ✅ Correct API endpoint
API_URL = "https://my.kudisms.net/api/sms"

# ✅ Validate required inputs
if not KUDI_API_KEY:
    print("\n❌ ERROR: Missing KUDI_API_KEY.\n")
    exit(1)

# Convert CSV numbers into list, strip '+' and ensure format starts with '234'
recipients_list = [num.strip().lstrip('+') for num in RECIPIENTS.split(",") if num.strip()]

# Header / log formatting
print("\n============================================================")
print("✅ KudiSMS BULK SENDER")
print("============================================================\n")
print(f"📱 Recipients Count: {len(recipients_list)}")
print(f"📤 Sender ID: {SENDER_ID}")
print(f"💬 Message: {MESSAGE}")
print(f"🔗 API Endpoint: {API_URL}")
print("============================================================")
print("🚀 Starting SMS sending...\n")

# Prepare bulk recipients as comma-separated string
recipients_str = ",".join(recipients_list)

params = {
    "token": KUDI_API_KEY,
    "senderID": SENDER_ID,
    "recipients": recipients_str,
    "message": MESSAGE,
    "gateway": GATEWAY
}

try:
    response = requests.get(API_URL, params=params, timeout=15)
    resp_text = response.text.strip()
    
    try:
        resp_json = response.json()
        if resp_json.get("status") == "success":
            print(f" ✅ SUCCESS → {resp_text}")
            success = len(recipients_list)
            failed = 0
        else:
            print(f" ❌ FAILED → {resp_text}")
            success = 0
            failed = len(recipients_list)
    except ValueError:
        # If not JSON, check for 'OK' or similar
        if resp_text.upper().startswith("OK"):
            print(f" ✅ SUCCESS → {resp_text}")
            success = len(recipients_list)
            failed = 0
        else:
            print(f" ❌ FAILED → {resp_text}")
            success = 0
            failed = len(recipients_list)

except Exception as e:
    print(f" ⚠️ ERROR: {e}")
    success = 0
    failed = len(recipients_list)

# Final summary output
print("\n============================================================")
print("📊 DELIVERY REPORT")
print("============================================================")
print(f"✅ Successful: {success}")
print(f"❌ Failed: {failed}")
print(f"📱 Total: {len(recipients_list)}")
print("============================================================\n")
