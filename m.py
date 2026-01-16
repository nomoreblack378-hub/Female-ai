import time, json, os, requests, random, sys
from datetime import datetime
import pytz
from instagrapi import Client

# Force print for GitHub logs
def log(message):
    print(f"DEBUG: {message}", flush=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_ID = "746424351272036" 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": f"You are @{BOT_USERNAME}, a savage Indian girl. Reply in short Hinglish (max 15 words)."},
            {"role": "user", "content": f"User {username}: {user_message}"}
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
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            log(f"--- Scanning Chat at {current_time} ---")
            
            messages = cl.direct_messages(TARGET_GROUP_ID, amount=10)
            
            for msg in reversed(messages):
                if msg.id in processed_ids or str(msg.user_id) == my_id:
                    continue
                
                text = (msg.text or "").lower()
                log(f"📩 New Message: {text}")

                # Detection Logic
                is_mentioned = f"@{BOT_USERNAME}".lower() in text
                
                # Reply check (Fixed version)
                is_reply = False
                # Agar message object mein reply_to_message_id hai, toh check karein
                reply_data = getattr(msg, 'reply_to_message', None)
                if reply_data and str(reply_data.get('user_id')) == my_id:
                    is_reply = True
                
                if is_mentioned or is_reply:
                    log(f"🎯 Match Found! Mention: {is_mentioned}, Reply: {is_reply}")
                    reply = get_ai_reply(text, "User")
                    if reply:
                        time.sleep(random.randint(5, 10))
                        cl.direct_send(reply, thread_ids=[TARGET_GROUP_ID], reply_to_message_id=msg.id)
                        log(f"✅ Sent Reply: {reply}")
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Error: {e}")
        
        log("Sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
