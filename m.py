import time, json, os, requests, random
from datetime import datetime
import pytz
from instagrapi import Client

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
            {"role": "system", "content": f"You are @{BOT_USERNAME}, a savage Indian girl. Reply in short Hinglish."},
            {"role": "user", "content": f"User {username}: {user_message}"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"DEBUG: AI Error -> {e}")
        return None

def run_bot():
    cl = Client()
    cl.set_user_agent()

    print("DEBUG: Logging in...")
    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        print(f"✅ Logged in! My ID: {my_id}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_run = time.time()
    
    while (time.time() - start_run) < 1300:
        try:
            print(f"\n--- Scanning GC ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
            
            # Direct Thread fetch method
            threads = cl.direct_threads(amount=5)
            target_thread = None
            
            for thread in threads:
                if thread.id == TARGET_GROUP_ID:
                    target_thread = thread
                    break
            
            if not target_thread:
                print(f"⚠️ Warning: GC with ID {TARGET_GROUP_ID} not found in recent chats!")
                # Agar ID match nahi hui toh saari available IDs dikhayega
                print("Available Chat IDs:")
                for t in threads: print(f"-> {t.thread_title} : {t.id}")
            else:
                messages = target_thread.messages
                print(f"DEBUG: Found {len(messages)} messages in thread.")
                
                for msg in reversed(messages):
                    if msg.id in processed_ids or str(msg.user_id) == my_id:
                        continue
                    
                    text = (msg.text or "").lower()
                    print(f"📩 Incoming: {text}")

                    is_mentioned = f"@{BOT_USERNAME}".lower() in text
                    is_reply = msg.reply_to_message and str(msg.reply_to_message.user_id) == my_id
                    
                    if is_mentioned or is_reply:
                        print("🎯 Trigger Match! Generating AI reply...")
                        reply = get_ai_reply(text, "User")
                        if reply:
                            time.sleep(random.randint(5, 10))
                            cl.direct_send(reply, thread_ids=[TARGET_GROUP_ID], reply_to_message_id=msg.id)
                            print(f"✅ Reply Sent: {reply}")
                    
                    processed_ids.add(msg.id)

        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
        
        print(f"Waiting 60s...")
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
    
