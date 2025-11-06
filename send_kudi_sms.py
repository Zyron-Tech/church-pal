# send_kudi_sms.py
"""
KudiSMS sender with proper error handling and response parsing.
Usage: Set environment variables and run this script to send SMS via KudiSMS API.

Required Environment Variables:
    KUDI_USERNAME: Your KudiSMS account username
    KUDI_PASSWORD: Your KudiSMS account password
    SENDER_ID: Your approved sender ID (register in KudiSMS dashboard)
    RECIPIENTS: Comma-separated phone numbers in E.164 format (e.g., "+2348030000000,+2348090000000")

Optional Environment Variables:
    MESSAGE: Custom message text (overrides default)
    KUDI_API_URL: API endpoint (default: https://account.kudisms.net/api/)
    THROTTLE: Delay between sends in seconds (default: 0.6)

API Documentation: https://developer.kudisms.net/
Response Codes: https://documenter.getpostman.com/view/3378495/2s9YBxYFXe
"""
import os
import requests
import time
import sys

# === CONFIGURATION ===
# Default message (can be overridden by MESSAGE env var)
DEFAULT_MESSAGE = "Hello! This is a reminder from your church — we look forward to seeing you tomorrow. Blessings."

# KudiSMS API endpoint
API_URL = os.environ.get("KUDI_API_URL", "https://account.kudisms.net/api/")

# Read credentials & config from environment
KUDI_USERNAME = os.environ.get("KUDI_USERNAME")
KUDI_PASSWORD = os.environ.get("KUDI_PASSWORD")
SENDER_ID = os.environ.get("SENDER_ID", "")
RECIPIENTS = os.environ.get("RECIPIENTS", "")
MESSAGE = os.environ.get("MESSAGE", DEFAULT_MESSAGE)
# Handle empty or missing throttle env variable safely
raw_throttle = os.environ.get("THROTTLE", "").strip()
THROTTLE_SECONDS = float(raw_throttle) if raw_throttle else 0.6


# KudiSMS API Response Codes
RESPONSE_CODES = {
    "000": "✅ Success - Message received successfully",
    "009": "⚠️  Warning - Maximum 6 pages of SMS allowed",
    "100": "❌ Error - Invalid token provided",
    "101": "❌ Error - Account deactivated, contact admin",
    "103": "❌ Error - Gateway doesn't exist",
    "104": "❌ Error - Blocked message keyword(s)",
    "105": "❌ Error - Sender ID has been blocked",
    "106": "❌ Error - Sender ID doesn't exist",
    "107": "❌ Error - Invalid phone number",
    "108": "❌ Error - Too many recipients (max 100 per batch)",
    "109": "❌ Error - Insufficient credit balance",
    "111": "❌ Error - Only approved promotional sender ID allowed",
    "114": "❌ Error - No package attached to service",
    "187": "❌ Error - Request could not be processed",
    "188": "❌ Error - Sender ID is unapproved",
    "300": "❌ Error - Missing required parameters",
    "401": "❌ Error - Request could not be completed"
}


def parse_response(response_text):
    """
    Parse KudiSMS API response.
    
    KudiSMS returns either:
    - A numeric code (e.g., "000", "109") 
    - JSON response: {"status":"OK","count":1,"price":2} or {"error":"...","errno":"103"}
    
    Returns: (success: bool, message: str, code: str)
    """
    response_text = response_text.strip()
    
    # Check if response is JSON
    if response_text.startswith("{"):
        try:
            import json
            data = json.loads(response_text)
            
            # Success response
            if data.get("status") == "OK":
                count = data.get("count", "N/A")
                price = data.get("price", "N/A")
                return True, f"Message sent successfully! Recipients: {count}, Cost: {price} units", "000"
            
            # Error response
            if "error" in data:
                errno = data.get("errno", "unknown")
                error_msg = data.get("error", "Unknown error")
                code_desc = RESPONSE_CODES.get(errno, f"Unknown error code: {errno}")
                return False, f"{code_desc} - {error_msg}", errno
                
        except json.JSONDecodeError:
            pass
    
    # Check if response is a numeric code
    if response_text.isdigit():
        code = response_text
        message = RESPONSE_CODES.get(code, f"Unknown response code: {code}")
        success = code == "000"
        return success, message, code
    
    # Unknown response format
    return False, f"Unexpected API response: {response_text}", "unknown"


def send_single(phone, message):
    """
    Send one SMS via KudiSMS API.
    
    Args:
        phone: Recipient phone number (E.164 format recommended)
        message: SMS message text
        
    Returns:
        (success: bool, status_message: str, response_code: str)
    """
    # Prepare POST data
    data = {
        "username": KUDI_USERNAME,
        "password": KUDI_PASSWORD,
        "sender": SENDER_ID,
        "mobiles": phone,
        "message": message
    }
    
    try:
        # Send POST request to KudiSMS API
        resp = requests.post(API_URL, data=data, timeout=30)
        
        # Check HTTP status
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text}", f"HTTP_{resp.status_code}"
        
        # Parse API response
        success, message, code = parse_response(resp.text)
        return success, message, code
        
    except requests.exceptions.Timeout:
        return False, "Request timeout after 30 seconds", "TIMEOUT"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {e}", "CONN_ERROR"
    except Exception as e:
        return False, f"Unexpected error: {e}", "EXCEPTION"


def validate_phone_number(phone):
    """Basic validation for phone numbers."""
    phone = phone.strip()
    if not phone:
        return False, "Empty phone number"
    
    # Remove spaces and dashes
    phone_clean = phone.replace(" ", "").replace("-", "")
    
    # Check if it's a valid format (basic check)
    if not phone_clean.startswith("+") and not phone_clean.isdigit():
        return False, f"Invalid format: {phone}"
    
    # Nigerian numbers should be +234... or 234... or 0...
    if phone_clean.startswith("0") and len(phone_clean) == 11:
        # Convert 0803... to +2348...
        phone_clean = "+234" + phone_clean[1:]
    elif phone_clean.startswith("234") and not phone_clean.startswith("+"):
        phone_clean = "+" + phone_clean
    
    return True, phone_clean


def main():
    """Main execution function."""
    print("=" * 60)
    print("KudiSMS Bulk SMS Sender")
    print("=" * 60)
    
    # Validate required environment variables
    missing = []
    if not KUDI_USERNAME:
        missing.append("KUDI_USERNAME")
    if not KUDI_PASSWORD:
        missing.append("KUDI_PASSWORD")
    if not RECIPIENTS:
        missing.append("RECIPIENTS")
    
    if missing:
        print("\n❌ ERROR: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        print("\nExample:")
        print("  export KUDI_USERNAME='your_username'")
        print("  export KUDI_PASSWORD='your_password'")
        print("  export SENDER_ID='YourName'")
        print("  export RECIPIENTS='+2348012345678,+2348098765432'")
        sys.exit(1)
    
    # Parse and validate recipient numbers
    raw_numbers = [n.strip() for n in RECIPIENTS.split(",") if n.strip()]
    
    if not raw_numbers:
        print("\n❌ ERROR: No recipient numbers found in RECIPIENTS.")
        print("   Format: RECIPIENTS='+2348012345678,+2348098765432'")
        sys.exit(1)
    
    # Validate phone numbers
    validated_numbers = []
    for num in raw_numbers:
        is_valid, result = validate_phone_number(num)
        if is_valid:
            validated_numbers.append(result)
        else:
            print(f"⚠️  Skipping invalid number: {result}")
    
    if not validated_numbers:
        print("\n❌ ERROR: No valid phone numbers to send to.")
        sys.exit(1)
    
    # Display configuration
    print(f"\n📱 Recipients: {len(validated_numbers)} number(s)")
    print(f"📤 Sender ID: {SENDER_ID if SENDER_ID else '(default)'}")
    print(f"💬 Message: {MESSAGE[:50]}{'...' if len(MESSAGE) > 50 else ''}")
    print(f"⏱️  Throttle: {THROTTLE_SECONDS}s between sends")
    print(f"🔗 API URL: {API_URL}")
    print("\n" + "=" * 60)
    print("Starting SMS delivery...\n")
    
    # Send SMS to each recipient
    success_count = 0
    failed_count = 0
    
    for i, phone in enumerate(validated_numbers, 1):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{i}/{len(validated_numbers)}] [{timestamp}] Sending to {phone}...", end=" ")
        
        success, status_msg, code = send_single(phone, MESSAGE)
        
        if success:
            print(status_msg)
            success_count += 1
        else:
            print(status_msg)
            failed_count += 1
        
        # Throttle between sends (except for last message)
        if i < len(validated_numbers):
            time.sleep(THROTTLE_SECONDS)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DELIVERY SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📱 Total: {len(validated_numbers)}")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
