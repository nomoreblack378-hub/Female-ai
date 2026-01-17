import time, os, requests, random, sys
from datetime import datetime
import pytz
from instagrapi import Client

def log(message):
    # flush=True logs ko turant GitHub Actions terminal pe dikhayega
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
    
    # Agar reply detect hua toh context AI ko bhej rahe hain
    if context_message:
        user_content = f"Context (Someone swiped on your message): '{context_message}'\nUser {username} says: {user_message}"
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
    # High-End User Agent for full JSON metadata
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    log("Starting Final Bot Sequence...")
    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Active! Logged in as ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320: # 22 Minutes Runtime
        try:
            log(f"--- Scanning Chat ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            
            # Metadata fetch karne ka sabse powerful tarika
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

                # --- 🎯 THE FORCE DETECTION ENGINE ---
                try:
                    # Message ko dict mein convert karke check kar rahe hain (Most reliable)
                    msg_raw = msg.dict()
                    reply_meta = msg_raw.get('replied_to_message')
                    
                    if reply_meta:
                        # User ID match karna (Kya reply mere message par hai?)
                        r_user_id = str(reply_meta.get('user_id', ''))
                        if r_user_id == my_id:
                            is_reply_to_me = True
                            context_text = reply_meta.get('text', '')
                except Exception as e:
                    # Fallback check
                    r_obj = getattr(msg, 'replied_to_message', None)
                    if r_obj and str(getattr(r_obj, 'user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_obj, 'text', '')

                # Logs for debugging in GitHub
                log(f"📩 [{text[:15]}...] | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Target Found! Generating Response...")
                    
                    sender = "User"
                    try: 
                        # User metadata refresh
                        sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(4, 8))
                        try:
                            # Arguments Fix: thread_id, text, item_id (Positional only)
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Swipe Reply Sent: {reply_content}")
                        except Exception as e:
                            log(f"⚠️ Swipe Method Failed, Sending Normal: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Warning: {e}")
            if "500" in str(e): 
                log("🛑 Rate Limit! Sleeping for 5 mins...")
                time.sleep(300)
        
        time.sleep(45)

if __name__ == "__main__":
    run_bot()
    
