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
    
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 10 words). Be natural and sharp."
    
    # Context handling for AI
    if context_message:
        user_content = f"Someone replied to your msg '{context_message}': {user_message}"
    else:
        user_content = f"User {username}: {user_message}"

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
    # Powerful User-Agent for group metadata extraction
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Started! ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Deep Scanning Thread ---")
            
            # --- 🎯 THE FIX: FETCH FULL THREAD ---
            # Normal direct_messages swipe data hide kar deta hai. 
            # cl.direct_thread use karne se full JSON milta hai.
            thread = cl.direct_thread(TARGET_GROUP_ID)
            messages = thread.messages
            
            for msg in messages:
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- 🎯 SWIPE DETECTION ENGINE ---
                try:
                    # Method 1: Check Pydantic model dictionary
                    m_data = msg.dict() if hasattr(msg, 'dict') else msg.model_dump()
                    reply_info = m_data.get('replied_to_message')
                    
                    if reply_info:
                        # Kya reply mere message par hai?
                        if str(reply_info.get('user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = reply_info.get('text', '')
                except:
                    # Method 2: Direct attribute fallback
                    r_msg = getattr(msg, 'replied_to_message', None)
                    if r_msg and str(getattr(r_msg, 'user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_msg, 'text', '')

                # Logs ab 'Swipe: True' dikhayenge
                log(f"📩 [{text[:15]}] | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Match Found! Getting AI reply...")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(4, 7))
                        try:
                            # --- 🛠 POSITION ARGUMENTS FIX ---
                            # cl.direct_answer(text, thread_id, item_id)
                            # Keyword arguments hata diye hain taaki crash na ho
                            cl.direct_answer(reply_content, TARGET_GROUP_ID, msg.id)
                            log(f"✅ Swipe-Reply Sent!")
                        except Exception as e:
                            log(f"⚠️ Answer failed (Sending Normal): {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Error: {e}")
            if "500" in str(e): time.sleep(300)
        
        time.sleep(45)

if __name__ == "__main__":
    run_bot()
    
