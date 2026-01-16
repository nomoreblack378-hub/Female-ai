import time, os, requests, random
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
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 10 words). Be natural."
    user_content = f"Someone swiped on you: '{context_message}'. User {username}: {user_message}" if context_message else f"User {username}: {user_message}"
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    cl = Client()
    # Using a very specific User-Agent to trick Instagram into sending full metadata
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Active! ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Error: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Scanning Deep Chat ---")
            
            # 1. Force Refresh Thread to load latest metadata
            thread = cl.direct_thread(TARGET_GROUP_ID)
            
            # 2. Get messages from the thread object directly
            messages = thread.messages
            
            for msg in messages:
                # Sirf naye messages process karein
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # --- 🎯 ULTIMATE SWIPE DETECTION (JSON LEVEL) ---
                # Hum Direct object ke 'replied_to_message' ko deeper check karenge
                try:
                    # Method A: Direct Attribute check
                    if hasattr(msg, 'replied_to_message') and msg.replied_to_message:
                        # Kuch versions me ye dict hota hai, kuch me object
                        r_data = msg.replied_to_message
                        r_user_id = str(r_data.get('user_id', '')) if isinstance(r_data, dict) else str(getattr(r_data, 'user_id', ''))
                        
                        if r_user_id == my_id:
                            is_reply_to_me = True
                            context_text = r_data.get('text', '') if isinstance(r_data, dict) else getattr(r_data, 'text', '')

                    # Method B: Clip/Metadata check (for stickers/media replies)
                    if not is_reply_to_me and hasattr(msg, 'clip'):
                         # Instagram reels/posts replies often store metadata here
                         pass
                except: pass

                log(f"📩 Msg: {text[:15]}... | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Match Triggered! Preparing Savage Reply...")
                    
                    # Username fetch
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(3, 5))
                        try:
                            # Positional arguments fix: (thread_id, text, item_id)
                            # item_id msg.id hi hota hai jo swipe ke liye zaroori hai
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Swipe Reply Sent!")
                        except Exception as e:
                            log(f"⚠️ Direct Answer Error: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                            log(f"✅ Fallback Sent!")
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Error: {e}")
            if "500" in str(e): time.sleep(300)
        
        time.sleep(40)

if __name__ == "__main__":
    run_bot()
    
