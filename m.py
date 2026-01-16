import time, os, requests, random, sys
from datetime import datetime
import pytz
from instagrapi import Client

def log(message):
    print(f"DEBUG: {message}", flush=True)

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_ID = "746424351272036" 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def get_ai_reply(user_message, username, context_message=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Personality: Savage Indian Girl
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Use Hinglish. Max 10 words. Be short, natural and savage."
    
    if context_message:
        user_content = f"Context (Someone replied to you): {context_message}\nUser {username} says: {user_message}"
    else:
        user_content = f"User {username} says: {user_message}"

    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    cl = Client()
    # High-End Android User-Agent taaki full metadata fetch ho
    cl.set_user_agent("Instagram 269.0.0.18.231 Android (31/12; 480dpi; 1080x2214; Google; Pixel 7 Pro; cheetah; qcom; en_US; 443455127)")

    log("Starting Pro Login...")
    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Active! Bot ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320: # 22 mins cycle for GitHub Actions
        try:
            log(f"--- Scanning ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            # Amount thoda zyada taaki koi message miss na ho
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=20)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- 🎯 THE PERFECT DETECTION ENGINE ---
                try:
                    # 1. Check direct object attribute
                    r_msg = getattr(msg, 'replied_to_message', None) or getattr(msg, 'reply_to_message', None)
                    
                    # 2. Check deep JSON dictionary (Best for GitHub/Servers)
                    m_dict = msg.dict()
                    reply_data = m_dict.get('replied_to_message', {}) or m_dict.get('reply_to_message', {})
                    
                    if (r_msg and str(getattr(r_msg, 'user_id', '')) == my_id) or \
                       (reply_data and str(reply_data.get('user_id', '')) == my_id):
                        is_reply_to_me = True
                        context_text = getattr(r_msg, 'text', '') if r_msg else reply_data.get('text', '')
                except: pass

                log(f"📩 [{text[:15]}...] | Swipe: {is_reply_to_me}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Target Found! Processing...")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user
                                                  
