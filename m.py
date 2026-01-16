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
    
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 12 words). Be natural and savage."
    
    # Context dena zaroori hai swipe reply ke liye
    if context_message:
        user_content = f"Someone swiped on your message: '{context_message}'.\nUser {username} says: {user_message}"
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
    # High-quality User-Agent for better metadata fetching
    cl.set_user_agent("Instagram 269.0.0.18.231 Android (31/12; 480dpi; 1080x2214; Google; Pixel 7 Pro; cheetah; qcom; en_US; 443455127)")

    log("Starting Bot...")
    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Active! Bot ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320: # 22 min cycle for GitHub Actions
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

                # --- 🎯 IMPROVED SWIPE DETECTION ---
                try:
                    # Latest Pydantic method use kar rahe hain swipe check karne ke liye
                    m_data = msg.model_dump() 
                    reply_info = m_data.get('replied_to_message', {})
                    
                    if reply_info and str(reply_info.get('user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = reply_info.get('text', '')
                except:
                    # Fallback check
                    r_msg = getattr(msg, 'replied_to_message', None)
                    if r_msg and str(getattr(r_msg, 'user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_msg, 'text', '')

                log(f"📩 [{text[:15]}] | Swipe: {is_reply_to_me}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Match Found! Getting AI reply...")
                    
                    sender = "User"
                    try: 
                        # Sender ka username fetch karna natural reply ke liye
                        sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    
                    if reply_content:
                        time.sleep(random.randint(4, 7)) # Simulate typing
                        try:
                            # CORRECT ARGUMENTS: (thread_id, text, item_id)
                            # Ye aapke 'DirectMixin' wale error ko fix karega
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            log(f"✅ Swipe Reply Sent!")
                        except Exception as e:
                            log(f"⚠️ Swipe failed, normal send: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            if "500" in str(e):
                log("🛑 Instagram Limit! Resting 5 mins...")
                time.sleep(300)
            else:
                log(f"⚠️ Loop Warning: {e}")
        
        time.sleep(40) # Safety delay

if __name__ == "__main__":
    run_bot()
    
