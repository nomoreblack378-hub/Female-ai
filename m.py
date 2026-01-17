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
    
    # System prompt to keep it savage and short
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 10 words). Be natural and sharp."
    
    # Adding context if it's a swipe/reply
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
    # Updated User-Agent for better metadata extraction
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Active! Logged in as: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Deep Scan Start ---")
            
            # 🎯 THE FIX: Puray thread ko fetch karna metadata ke liye
            # Normal direct_messages() swipe data hide kar deta hai.
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
                    # Check if message is a reply to someone
                    # Method: Using dictionary dump to bypass Pydantic errors
                    m_dict = msg.dict() if hasattr(msg, 'dict') else msg.model_dump()
                    reply_data = m_dict.get('replied_to_message')
                    
                    if reply_data:
                        # Check if the replied-to message was sent by the BOT
                        if str(reply_data.get('user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = reply_data.get('text', '')
                except:
                    # Fallback for older Pydantic versions
                    r_obj = getattr(msg, 'replied_to_message', None)
                    if r_obj and str(getattr(r_obj, 'user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = getattr(r_obj, 'text', '')

                # Logs ab 'Swipe: True' dikhayenge agar metadata match hua
                log(f"📩 Msg: {text[:10]}... | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Match Found! Preparing Response...")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    
                    if reply_content:
                        time.sleep(random.randint(4, 7)) # Anti-spam delay
                        try:
                            # --- 🛠 POSITION ARGUMENTS FIX ---
                            # Arguments order for instagrapi 2.2.1: (text, thread_id, item_id)
                            # Keyword arguments hata diye hain taaki crash na ho
                            cl.direct_answer(reply_content, TARGET_GROUP_ID, msg.id)
                            log(f"✅ Swipe Reply Sent!")
                        except Exception as e:
                            log(f"⚠️ Answer failed: {e}. Using direct_send fallback.")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Error: {e}")
            if "500" in str(e): 
                log("Server error, sleeping 5 mins...")
                time.sleep(300)
        
        time.sleep(45)

if __name__ == "__main__":
    run_bot()
    
