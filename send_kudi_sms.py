# send_kudi_sms.py
"""
Simple KudiSMS sender.
Usage: this script reads env vars (KUDI_USERNAME, KUDI_PASSWORD, SENDER_ID, RECIPIENTS)
and sends MESSAGE to each recipient using KudiSMS API.

RECIPIENTS: comma-separated E.164 numbers, e.g. "+2348030000000,+2348090000000"
DOCUMENTATION: https://developer.kudisms.net/ (KudiSMS API)
"""

import os
import requests
import time

# === CONFIG ===
# Hardcoded message (change this to whatever you want)
MESSAGE = "Hello! This is a reminder from your church — we look forward to seeing you tomorrow. Blessings."

# KudiSMS API base used in their examples / sample scripts
API_URL = os.environ.get("KUDI_API_URL", "https://account.kudisms.net/api/")  # default based on their sample scripts

# Read credentials & targets from env
KUDI_USERNAME = os.environ.get("KUDI_USERNAME")
KUDI_PASSWORD = os.environ.get("KUDI_PASSWORD")
SENDER_ID = os.environ.get("SENDER_ID")  # submit/approve a sender in Kudi dashboard if you want a name
RECIPIENTS = os.environ.get("RECIPIENTS", "")  # comma-separated numbers

THROTTLE_SECONDS = float(os.environ.get("THROTTLE", "0.6"))  # friendly delay between sends

def send_single(phone, message):
    """
    Send one SMS via KudiSMS POST API.
    Form parameters used follow Kudi sample scripts: username, password, sender, mobiles, message
    (If your account requires extra fields, adapt accordingly.)
    """
    data = {
        "username": KUDI_USERNAME,
        "password": KUDI_PASSWORD,
        "sender": SENDER_ID or "",
        "mobiles": phone,
        "message": message
    }

    try:
        resp = requests.post(API_URL, data=data, timeout=30)
    except Exception as e:
        return False, f"Request error: {e}"

    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}: {resp.text}"

    # Kudi returns a short code/response in the body (000 => success etc.); return raw for now
    return True, resp.text.strip()

def main():
    missing = [k for k in ("KUDI_USERNAME","KUDI_PASSWORD","RECIPIENTS") if not os.environ.get(k)]
    if missing:
        print("Missing required env vars:", ", ".join(missing))
        print("Set KUDI_USERNAME, KUDI_PASSWORD and RECIPIENTS (comma-separated).")
        return

    numbers = [n.strip() for n in RECIPIENTS.split(",") if n.strip()]
    if not numbers:
        print("No recipient numbers found in RECIPIENTS.")
        return

    print(f"Sending message to {len(numbers)} recipient(s)...")
    for phone in numbers:
        ok, resp = send_single(phone, MESSAGE)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        if ok:
            print(f"[{timestamp}] ✅ Sent to {phone} — Kudi response: {resp}")
        else:
            print(f"[{timestamp}] ❌ Failed to {phone} — Error: {resp}")
        time.sleep(THROTTLE_SECONDS)

    print("Done.")

if __name__ == "__main__":
    main()
