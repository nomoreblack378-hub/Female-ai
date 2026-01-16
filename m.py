import time, os, requests, random
from datetime import datetime
import pytz
from instagrapi import Client

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_ID = "746424351272036" 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def get_ai_reply(user_message, username, context_message=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. Reply in short Hinglish (max 10 words)."
    # Swipe context AI ko dena
    user_content = f"User {username} swiped on your msg '{context_message}': {user_message}" if context_message else f"User {username}: {user_message}"

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
    # User-Agent updated for swipe detection
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2214; Google; Pixel 5; redfin; qcom; en_US; 340011805)")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        print(f"✅ Logged in! My ID: {my_id}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    
    while True:
        try:
            print(f"--- Scanning Chat ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=10)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    processed_ids.add(msg.id)
                    continue
                
                text = (msg.text or "").lower()
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                is_reply_to_me = False
                context_text = None

                # Swipe detection logic
                try:
                    m_dict = msg.dict() # Force scan dictionary
                    reply_info = m_dict.get('replied_to_message', {})
                    if reply_info and str(reply_info.get('user_id', '')) == my_id:
                        is_reply_to_me = True
                        context_text = reply_info.get('text', '')
                except: pass

                # Agar swipe hai ya mention hai
                if is_mentioned or is_reply_to_me:
                    print(f"🎯 Match Triggered! Swipe: {is_reply_to_me}")
                    
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(5, 10))
                        try:
                            # CORRECT SYNTAX: direct_answer(thread_id, text, item_id)
                            # Ye aapke 'direct_answer' logic ko sahi tareeke se execute karega
                            cl.direct_answer(TARGET_GROUP_ID, reply_content, msg.id)
                            print(f"✅ Swipe-Reply Sent: {reply_content}")
                        except Exception as e:
                            print(f"⚠️ Swipe failed, sending normal: {e}")
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                
                processed_ids.add(msg.id)

        except Exception as e:
            print(f"⚠️ Loop Warning: {e}")
            if "500" in str(e): time.sleep(300) # Rate limit protection
        
        time.sleep(45)

if __name__ == "__main__":
    run_bot()
    
