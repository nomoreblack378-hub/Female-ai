import time, json, os, requests, random, sys
from datetime import datetime
import pytz
from instagrapi import Client

def log(message):
    print(f"DEBUG: {message}", flush=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_ID = "746424351272036" 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": f"You are @{BOT_USERNAME}, a witty and savage Indian girl. Reply in short Hinglish (max 15 words). Be very natural."},
            {"role": "user", "content": f"User {username}: {user_message}"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        log(f"AI Error -> {e}")
        return None

def run_bot():
    cl = Client()
    cl.set_user_agent()

    log("Starting login process...")
    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Logged in! My ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Scanning Chat ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=10)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    continue
                
                text = (msg.text or "").lower()
                log(f"📩 Incoming: {text}")

                # 1. Mention Detection
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                
                # 2. Swipe/Slide Reply Detection (FIXED)
                is_reply_to_me = False
                # Instagrapi mein reply_to_message ek dictionary ho sakti hai ya object
                reply_val = getattr(msg, 'reply_to_message', None)
                if reply_val:
                    # Agar dictionary hai toh .get() use karenge, agar object hai toh .user_id
                    reply_user_id = str(reply_val.get('user_id', '')) if isinstance(reply_val, dict) else str(getattr(reply_val, 'user_id', ''))
                    if reply_user_id == my_id:
                        is_reply_to_me = True
                
                if is_mentioned or is_reply_to_me:
                    log(f"🎯 Match! Mention: {is_mentioned}, Swipe-Reply: {is_reply_to_me}")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender)
                    if reply_content:
                        time.sleep(random.randint(4, 7)) # Human delay
                        cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                        log(f"✅ Sent Reply: {reply_content}")
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Warning: {e}")
        
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
    
