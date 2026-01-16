import time, os, requests, random
from datetime import datetime
import pytz
from instagrapi import Client

# Log function for real-time visibility in GitHub Actions
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
    system_content = f"You are @{BOT_USERNAME}, a savage Indian girl. Reply in short Hinglish (max 10 words)."
    user_content = f"Someone replied to your msg '{context_message}': {user_message}" if context_message else f"User {username}: {user_message}"
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    cl = Client()
    # Force Mobile User-Agent to get better swipe metadata
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Started! ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Error: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Scanning Chat ---")
            # Thread refresh taaki metadata fetch ho sake
            cl.direct_thread(TARGET_GROUP_ID) 
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=15)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- 🎯 THE ULTIMATE SWIPE DETECTION ---
                try:
                    # Method 1: Check if 'replied_to_message' exists in object
                    if hasattr(msg, 'replied_to_message') and msg.replied_to_message:
                        if str(msg.replied_to_message['user_id']) == my_id:
                            is_reply_to_me = True
                            context_text = msg.replied_to_message.get('text', '')
                    
                    # Method 2: Check via Dict dump if Method 1 fails
                    if not is_reply_to_me:
                        m_dict = msg.dict()
                        r_info = m_dict.get('replied_to_message')
                        if r_info and str(r_info.get('user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = r_info.get('text', '')
                except Exception as e:
                    pass

                # Force Log to see why it's failing
                log(f"📩 Msg: {text[:10]}... | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Match Triggered!")
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(3, 5))
                        # Fix for direct_answer arguments
                        try:
                            # Hum thread_id, text, aur item_id ko correct order mein bhej rahe hain
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Reply Sent Successfully!")
                        except:
                            # Fallback if direct_answer still fails
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                            log(f"✅ Fallback Reply Sent!")
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Error: {e}")
            if "500" in str(e): time.sleep(300)
        
        time.sleep(40)

if __name__ == "__main__":
    run_bot()
    
