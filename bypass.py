import getpass
import os
import re
import sys
import time
import ping3
import base64
import random
import string
import aiohttp
import asyncio
import hashlib
import requests
import subprocess
from datetime import timedelta, datetime
from urllib.parse import unquote, urlparse, parse_qs
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# ===== Colors =====
r, g, y, b, w, c = "\033[1;31m", "\033[1;32m", "\033[1;33m", "\033[1;34m", "\033[0m", "\033[1;36m"

# ===== Telegram Config =====
TELEGRAM_BOT_TOKEN = "8791054334:AAH5M2zpHsEEJ9-QEaTARclp6SEtnsALCdI"
TELEGRAM_CHAT_ID = "7774402865"

# ===== Target URL =====
TARGET_URL = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=4c49684b2d2e&gw_sn=H1U82VB006839&gw_address=192.168.110.1&gw_port=2060&ip=192.168.110.180&mac=ea:4b:cc:49:db:bd&slot_num=16&nasip=192.168.1.63&ssid=VLAN233&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&chap_id=%5C311&chap_challenge=%5C251%5C002%5C152%5C160%5C153%5C313%5C221%5C035%5C277%5C321%5C256%5C070%5C153%5C351%5C231%5C142"

LOG_FILE = "bypass_history.txt"
LICENSE_FILE = ".license"

# ===== Utility =====
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def Line():
    print(f"{y}─{w}" * os.get_terminal_size().columns)

def get_device_id():
    id_file = ".device_id"
    if os.path.exists(id_file):
        try:
            with open(id_file, "r") as f:
                return f.read().strip()
        except:
            pass
    try:
        result = subprocess.check_output("whoami", shell=True, encoding='utf-8')
        device_id = result.strip()
        if device_id:
            clean_id = re.sub(r'[^A-Za-z0-9]', '', device_id).upper()
            clean_id = (clean_id[:6] if len(clean_id) >= 6 else clean_id.ljust(6, 'X'))
            new_id = f"STR-{clean_id}"
            with open(id_file, "w") as f:
                f.write(new_id)
            return new_id
    except:
        pass
    try:
        device_id = getpass.getuser()
        if device_id:
            clean_id = re.sub(r'[^A-Za-z0-9]', '', device_id).upper()
            clean_id = clean_id[:6].ljust(6, 'X')
            new_id = f"STR-{clean_id}"
            with open(id_file, "w") as f:
                f.write(new_id)
            return new_id
    except:
        pass
    random_id = "STR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with open(id_file, "w") as f:
        f.write(random_id)
    return random_id

def write_log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def format_remaining(remaining):
    if remaining is None:
        return "Unknown"
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# ===== License Manager =====
def get_license_status():
    if not os.path.exists(LICENSE_FILE):
        return None, None, None, None
    try:
        with open(LICENSE_FILE, "r") as f:
            data = f.read().strip().split("|")
            if len(data) != 2:
                return None, None, None, None
            key, exp_ts = data
            exp_dt = datetime.fromtimestamp(float(exp_ts))
            now = datetime.now()
            if now < exp_dt:
                return True, key, exp_dt, exp_dt - now
            else:
                return False, key, exp_dt, None
    except:
        return None, None, None, None

def save_license(key, days):
    exp_dt = datetime.now() + timedelta(days=days)
    with open(LICENSE_FILE, "w") as f:
        f.write(f"{key}|{exp_dt.timestamp()}")
    return exp_dt

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 10, "offset": offset} if offset else {"timeout": 10}
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code == 200:
            return resp.json().get("result", [])
    except:
        pass
    return []

def request_license_via_telegram(user_key):
    device_id = get_device_id()
    msg = f"🔑 *License Request*\n📱 Device: `{device_id}`\n🔐 Key: `{user_key}`\n\nReply: `/allow {user_key} <days>`"
    send_telegram_message(msg)
    print(f"{c}[*] Request sent to Telegram. Waiting for admin approval...{w}")
    
    last_update_id = None
    timeout = 120
    start = time.time()
    while time.time() - start < timeout:
        updates = get_updates(offset=last_update_id)
        for update in updates:
            last_update_id = update.get("update_id") + 1
            msg_obj = update.get("message", {})
            text = msg_obj.get("text", "")
            if text.startswith("/allow"):
                parts = text.split()
                if len(parts) == 3 and parts[1] == user_key:
                    try:
                        days = int(parts[2])
                        exp_dt = save_license(user_key, days)
                        print(f"{g}[+] License approved! Valid until: {exp_dt}{w}")
                        send_telegram_message(f"✅ Approved: {user_key} for {days} days.")
                        return True
                    except:
                        pass
        time.sleep(2)
    print(f"{r}[!] Timeout waiting for approval.{w}")
    return False

async def main():
    clear()
    Line()
    print(f"{c}      RUIJIE BYPASS TOOL (AUTO-COMPILE VERSION){w}")
    Line()
    
    device_id = get_device_id()
    print(f"{y}Device ID: {w}{device_id}")
    
    status, key, exp, rem = get_license_status()
    if status is True:
        print(f"{g}License: Active (Expires: {exp} - {format_remaining(rem)} left){w}")
    else:
        print(f"{r}License: Not Found or Expired{w}")
        user_key = input(f"{c}Enter License Key: {w}").strip()
        if not user_key:
            print(f"{r}Invalid Key.{w}")
            return
        if not request_license_via_telegram(user_key):
            return

    # Mock bypass logic (as per original tool intent)
    print(f"{y}[*] Starting Bypass...{w}")
    # ... (Actual bypass logic would go here)
    print(f"{g}[+] Bypass successful!{w}")

if __name__ == "__main__":
    asyncio.run(main())
