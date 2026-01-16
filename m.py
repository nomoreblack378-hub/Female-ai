import time, os, requests, random, sys
from datetime import datetime
import pytz
from instagrapi import Client

def log(message):
    print(f"DEBUG: {message}", flush=True)

# --- Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_ID = "746424351272036" 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def get_ai_reply(user_message, username, context_message=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    system_content = f"You are @{BOT_USERNAME}, a savage Indian girl. Reply in Hinglish. Max 10 words. Be natural."
    user_content = f"Context: {context_message}\nUser {username}: {user_message}" if context_message else f"User {username}: {user_message}"
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    cl = Client()
    # High-end user agent taaki swipe metadata miss na ho
    cl.set_user_agent("Instagram 269.0.0.18.231 Android (31/12; 480dpi; 1080x2214; Google; Pixel 7 Pro; cheetah; qcom; en_US; 443455127)")

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
            log(f"--- Scanning ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=20)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- 🎯 THE DEEP SCAN (Swipe Detection) ---
                try:
                    # Method 1: model_dump (Pydantic v2)
                    m_data = msg.model_dump()
                    r_info = m_data.get('replied_to_message', {})
                    if r_info and str(r_info.get('user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = r_info.get('text', '')
                    
                    # Method 2: Fallback for older metadata
                    if not is_reply_to_me:
                        r_msg = getattr(msg, 'replied_to_message', None)
                        if r_msg and str(getattr(r_msg, 'user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = getattr(r_msg, 'text', '')
                except: pass

                # Log swipe status for debugging
                if is_mentioned or is_reply_to_me:
                    log(f"🎯 Match! Mention: {is_mentioned}, Swipe: {is_reply_to_me}")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(4, 7))
                        try:
                            # --- 🛠 THE FIX FOR "3 POSITIONAL ARGUMENTS" ERROR ---
                            # Hum explicitly bata rahe hain ki kaunsa argument kya hai
                            cl.direct_answer(
                                text=reply_content,
                                thread_id=TARGET_GROUP_ID,
                                item_id=msg.id
                            )
                            log(f"✅ Sent Swipe Reply!")
                        except Exception as e:
                            log(f"⚠️ Swipe Failed: {e}. Trying Normal Send...")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Warning: {e}")
            if "500" in str(e): time.sleep(300)
        
        time.sleep(40)

if __name__ == "__main__":
    run_bot()
    
