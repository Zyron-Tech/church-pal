"""
Church Bulk SMS Automation - KudiSMS Version with Google Sheets
Author: Peace Mathew
This script sends personalized SMS messages to church members
via KudiSMS API using data from Google Sheets.
"""
import os
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from datetime import datetime
import time
import json

# Load environment variables
load_dotenv()

# 🔐 API Credentials
KUDI_API_KEY = os.getenv("KUDI_API_KEY")
GOOGLE_SHEETS_CREDS = os.getenv("GOOGLE_SHEETS_CREDS")  # JSON credentials as string
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
API_URL = "https://my.kudisms.net/api/sms"

def connect_to_sheets():
    """Connect to Google Sheets"""
    try:
        print("🔗 Connecting to Google Sheets...")
        
        # Parse credentials from environment variable
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        print("✅ Connected to Google Sheets successfully!\n")
        return sheet
    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
        exit(1)

def get_settings(sheet):
    """Get settings from the Settings sheet"""
    try:
        settings_sheet = sheet.worksheet("Settings")
        settings_data = settings_sheet.get_all_records()
        
        # Convert list of dicts to a single settings dict
        settings = {}
        for row in settings_data:
            if row.get('setting_name') and row.get('value'):
                settings[row['setting_name']] = row['value']
        
        print("⚙️ Settings loaded:")
        print(f"   Sender ID: {settings.get('sender_id', 'Not set')}")
        print(f"   Gateway: {settings.get('gateway', 'Not set')}")
        print(f"   Message Template: {settings.get('message_template', 'Not set')[:50]}...")
        print()
        
        return settings
    except Exception as e:
        print(f"⚠️ Could not load settings: {e}")
        print("Using default settings...\n")
        return {
            'sender_id': 'ChurchBot',
            'gateway': '2',
            'message_template': 'Hello {name}, this is a message from our church. God bless you!'
        }

def get_members(sheet):
    """Get member data from the Members sheet"""
    try:
        members_sheet = sheet.worksheet("Members")
        members_data = members_sheet.get_all_records()
        
        print(f"📋 Found {len(members_data)} members in the database\n")
        return members_data
    except Exception as e:
        print(f"❌ Error reading members: {e}")
        exit(1)

def personalize_message(template, member):
    """Replace placeholders in message template with member data"""
    message = template
    
    # Available placeholders: {name}, {gender}, {address}, {church_name}
    replacements = {
        '{name}': member.get('name', ''),
        '{first_name}': member.get('name', '').split()[0] if member.get('name') else '',
        '{gender}': member.get('gender', ''),
        '{address}': member.get('address', ''),
    }
    
    for placeholder, value in replacements.items():
        message = message.replace(placeholder, str(value))
    
    return message

def send_sms(phone, message, sender_id, gateway):
    """Send SMS to a single recipient"""
    # Clean phone number
    phone = phone.strip().lstrip('+')
    
    # Ensure Nigerian format
    if phone.startswith('0'):
        phone = '234' + phone[1:]
    elif not phone.startswith('234'):
        phone = '234' + phone
    
    params = {
        "token": KUDI_API_KEY,
        "senderID": sender_id,
        "recipients": phone,
        "message": message,
        "gateway": gateway
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        resp_text = response.text.strip()
        
        try:
            resp_json = response.json()
            return resp_json.get("status") == "success", resp_text
        except ValueError:
            # If not JSON, check for 'OK'
            return resp_text.upper().startswith("OK"), resp_text
    except Exception as e:
        return False, str(e)

def main():
    print("\n" + "="*60)
    print("✝️  CHURCH SMS AUTOMATION SYSTEM")
    print("="*60 + "\n")
    print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Validate API key
    if not KUDI_API_KEY:
        print("❌ ERROR: Missing KUDI_API_KEY\n")
        exit(1)
    
    if not GOOGLE_SHEETS_CREDS:
        print("❌ ERROR: Missing GOOGLE_SHEETS_CREDS\n")
        exit(1)
    
    if not SPREADSHEET_ID:
        print("❌ ERROR: Missing SPREADSHEET_ID\n")
        exit(1)
    
    # Connect to Google Sheets
    sheet = connect_to_sheets()
    
    # Get settings and members
    settings = get_settings(sheet)
    members = get_members(sheet)
    
    # Extract settings
    sender_id = settings.get('sender_id', 'ChurchBot')
    gateway = settings.get('gateway', '2')
    message_template = settings.get('message_template', 
                                    'Hello {name}, this is a message from our church. God bless you!')
    
    # Filter active members with valid phone numbers
    valid_members = []
    for member in members:
        phone = str(member.get('phone', '')).strip()
        status = str(member.get('status', 'active')).lower()
        
        if phone and status == 'active':
            valid_members.append(member)
    
    print(f"📱 Valid Active Members: {len(valid_members)}")
    print(f"📤 Sender ID: {sender_id}")
    print(f"🔗 API Endpoint: {API_URL}")
    print("="*60)
    print("🚀 Starting SMS campaign...\n")
    
    # Send messages
    success_count = 0
    failed_count = 0
    results = []
    
    for i, member in enumerate(valid_members, 1):
        name = member.get('name', 'Member')
        phone = member.get('phone', '')
        
        # Personalize message
        personalized_msg = personalize_message(message_template, member)
        
        print(f"[{i}/{len(valid_members)}] Sending to {name} ({phone})...")
        
        # Send SMS
        success, response = send_sms(phone, personalized_msg, sender_id, gateway)
        
        if success:
            print(f"    ✅ SUCCESS\n")
            success_count += 1
            results.append({
                'name': name,
                'phone': phone,
                'status': 'Success',
                'response': response
            })
        else:
            print(f"    ❌ FAILED: {response}\n")
            failed_count += 1
            results.append({
                'name': name,
                'phone': phone,
                'status': 'Failed',
                'response': response
            })
        
        # Rate limiting: wait 1 second between messages
        if i < len(valid_members):
            time.sleep(1)
    
    # Update delivery log in Google Sheets
    try:
        log_sheet = sheet.worksheet("Delivery_Log")
    except:
        # Create log sheet if it doesn't exist
        log_sheet = sheet.add_worksheet(title="Delivery_Log", rows="1000", cols="6")
        log_sheet.append_row(['Timestamp', 'Name', 'Phone', 'Status', 'Response', 'Message'])
    
    # Append results to log
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for result in results:
        log_sheet.append_row([
            timestamp,
            result['name'],
            result['phone'],
            result['status'],
            result['response'],
            personalize_message(message_template, 
                              {'name': result['name']})[:50] + '...'
        ])
    
    # Final summary
    print("\n" + "="*60)
    print("📊 DELIVERY REPORT")
    print("="*60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📱 Total Sent: {len(valid_members)}")
    print(f"💾 Log saved to Google Sheets")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
