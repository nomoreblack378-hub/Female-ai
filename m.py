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
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 12 words). Be natural."
    user_content = f"User {username} swiped on your msg '{context_message}': {user_message}" if context_message else f"User {username}: {user_message}"
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    cl = Client()
    # High-quality Android User-Agent taaki extra data fetch ho sake
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

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
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- ⚠️ FORCE DETECTION LOGIC ⚠️ ---
                # Kabhi kabhi instagrapi replied_to_message miss kar deta hai. 
                # Hum message dict ko check karenge manually.
                
                try:
                    # Method 1: Check deep metadata dictionary
                    msg_dict = msg.dict()
                    reply_data = msg_dict.get('replied_to_message', {})
                    
                    if reply_data:
                        r_user_id = str(reply_data.get('user_id', ''))
                        if r_user_id == my_id:
                            is_reply_to_me = True
                            context_text = reply_data.get('text', '')
                    
                    # Method 2: Check standard object attributes
                    elif hasattr(msg, 'reply_to_message') and msg.reply_to_message:
                        if str(msg.reply_to_message.user_id) == my_id:
                            is_reply_to_me = True
                            context_text = msg.reply_to_message.text
                except:
                    pass

                log(f"📩 Incoming: {text} | Swipe: {is_reply_to_me}")

                if is_mentioned or is_reply_to_me:
                    log(f"🎯 Match Triggered!")
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    
                    if reply_content:
                        time.sleep(random.randint(5, 10))
                        try:
                            # Terminal Error fix: positional arguments (text, thread_id, item_id)
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Swipe-Reply Sent!")
                        except Exception as e:
                            log(f"⚠️ Answer failed: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            if "500" in str(e): #
                log("🛑 Instagram Blocked! Waiting 5 mins...")
                time.sleep(300)
            else:
                log(f"⚠️ Loop Warning: {e}")
        
        time.sleep(40)

if __name__ == "__main__":
    run_bot()
    
