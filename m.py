import time
import json
import os
import requests
import random
from datetime import datetime
import pytz
from instagrapi import Client

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_IDS = ["746424351272036"] 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def is_sleeping_time():
    now = datetime.now(IST)
    return now.hour >= 0 and now.hour < 7

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    system_prompt = (
        f"You are @{BOT_USERNAME}, a witty, savage, and flirty Indian girl. "
        "Reply in Hinglish. Keep it extremely short (max 15 words). "
        "Never mention you are an AI. Be real and charmingly rude."
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User {username} said: {user_message}"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except:
        return None

def run_bot():
    if is_sleeping_time():
        print("😴 Raat ho gayi hai. Anti-ban sleep mode active.")
        return

    cl = Client()
    cl.set_user_agent()

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        print(f"✅ Logged in! Bot: {BOT_USERNAME} | ID: {my_id}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    if os.path.exists('processed.json'):
        with open('processed.json', 'r') as f:
            try: processed_ids = set(json.load(f))
            except: pass

    start_run = time.time()
    # 22 minute tak workflow chalega
    while (time.time() - start_run) < 1320:
        for group_id in TARGET_GROUP_IDS:
            try:
                # Naya Method: cl.direct_messages use kiya hai jo zyada reliable hai
                messages = cl.direct_messages(group_id, amount=10)
                
                for msg in reversed(messages):
                    if msg.id in processed_ids:
                        continue
                    
                    # Khud ke messages ko ignore karein
                    if str(msg.user_id) == my_id:
                        processed_ids.add(msg.id)
                        continue

                    text = (msg.text or "").lower()
                    
                    # Detection logic
                    is_mentioned = f"@{BOT_USERNAME}".lower() in text
                    is_reply_to_me = False
                    
                    if msg.reply_to_message and str(msg.reply_to_message.user_id) == my_id:
                        is_reply_to_me = True

                    if is_mentioned or is_reply_to_me:
                        print(f"🎯 Message Detected! Text: {text}")
                        
                        # Simulating Human Thinking
                        time.sleep(random.uniform(5, 10))
                        
                        sender = "Friend"
                        try:
                            # User info fetch karna taaki AI ko naam pata chale
                            sender = cl.user_info_v1(msg.user_id).username
                        except: pass
                        
                        ai_response = get_ai_reply(text, sender)
                        
                        if ai_response:
                            # Simulating Typing
                            typing_delay = len(ai_response) * 0.12 + random.uniform(2, 5)
                            print(f"⌨️ Typing for {typing_delay:.1f}s...")
                            time.sleep(min(typing_delay, 12))
                            
                            cl.direct_send(ai_response, thread_ids=[group_id], reply_to_message_id=msg.id)
                            print(f"✅ Successfully replied to {sender}")
                        else:
                            print("⚠️ AI couldn't generate a reply.")
                    
                    processed_ids.add(msg.id)

            except Exception as e:
                print(f"⚠️ Loop Warning: {e}")
                if "429" in str(e):
                    print("🚨 Rate limit hit. Exiting to stay safe.")
                    return

        # Tracking update karein
        with open('processed.json', 'w') as f:
            json.dump(list(processed_ids)[-100:], f)
            
        wait = random.randint(60, 120)
        print(f"😴 Waiting {wait}s for next check...")
        time.sleep(wait)

if __name__ == "__main__":
    run_bot()
    
