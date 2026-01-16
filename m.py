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
    
    system_content = f"You are @{BOT_USERNAME}, a witty and savage Indian girl. Reply in short Hinglish (max 15 words). Be natural and funny."
    
    if context_message:
        user_content = f"User {username} replied to message: '{context_message}'. User said: '{user_message}'"
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
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=20)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                
                # Detection Logic
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None
                
                replied_msg = getattr(msg, 'replied_to_message', None)
                if replied_msg:
                    r_user_id = str(replied_msg.get('user_id', '')) if isinstance(replied_msg, dict) else str(getattr(replied_msg, 'user_id', ''))
                    if r_user_id == my_id:
                        is_reply_to_me = True
                        context_text = replied_msg.get('text', '') if isinstance(replied_msg, dict) else getattr(replied_msg, 'text', '')

                # Response Trigger
                if is_mentioned or is_reply_to_me:
                    log(f"🎯 Trigger: Mention={is_mentioned}, Swipe={is_reply_to_me}")
                    
                    sender_username = "User"
                    try: sender_username = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender_username, context_text)
                    
                    if reply_content:
                        time.sleep(random.randint(4, 7))
                        
                        # --- KEY CHANGE: Swipe karke reply dena ---
                        # direct_answer function use karke bot usi message par swipe karega
                        try:
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Sent Swipe-Reply to {sender_username}")
                        except Exception as send_err:
                            log(f"Fallback to normal send: {send_err}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Warning: {e}")
        
        time.sleep(20)

if __name__ == "__main__":
    run_bot()
    
