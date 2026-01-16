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

def get_ai_reply(user_message, username, context_message=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_content = f"You are @{BOT_USERNAME}, a witty and savage Indian girl. Reply in short Hinglish (max 15 words). Be natural."
    if context_message:
        user_content = f"User {username} swiped on your msg '{context_message}': {user_message}"
    else:
        user_content = f"User {username}: {user_message}"

    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except:
        return None

def run_bot():
    cl = Client()
    # User agent change karna zaroori hai swipe detection ke liye
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x2214; ASUS; ASUS_I003D; I003D; qcom; en_US; 340011805)")

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
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                
                # --- NEW DEEP DETECTION LOGIC ---
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None
                
                # 1. Check for 'reply_to_message' attribute directly
                if hasattr(msg, 'reply_to_message') and msg.reply_to_message:
                    r_msg = msg.reply_to_message
                    r_user_id = str(getattr(r_msg, 'user_id', ''))
                    if r_user_id == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_msg, 'text', '')

                # 2. Check for 'replied_to_message' as a fallback
                elif hasattr(msg, 'replied_to_message') and msg.replied_to_message:
                    r_msg = msg.replied_to_message
                    r_user_id = str(getattr(r_msg, 'user_id', ''))
                    if r_user_id == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_msg, 'text', '')

                log(f"📩 Incoming: {text} | Swipe: {is_reply_to_me}")

                if is_mentioned or is_reply_to_me:
                    log(f"🎯 Match Triggered!")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    
                    if reply_content:
                        time.sleep(random.randint(5, 8))
                        
                        # --- FIXING THE direct_answer ERROR ---
                        try:
                            # Hum Bina keyword arguments (item_id=...) ke bhejenge
                            # Taaki positional arguments use ho
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Swipe Reply Success!")
                        except Exception as e:
                            log(f"⚠️ Swipe failed, sending normal: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            # Agar 500 Error aaye toh break lelo
            if "500" in str(e):
                log("🛑 Instagram Blocked! Sleeping for 5 mins...")
                time.sleep(300)
            else:
                log(f"⚠️ Loop Warning: {e}")
        
        time.sleep(40)

if __name__ == "__main__":
    run_bot()
    
