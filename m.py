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
BOT_USERNAME = "mo.chi.351"  # Updated username
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
        "Be very natural. If someone mentions you or replies to you, be charmingly savage."
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
        print("😴 Raat ke 12-7 baje hain. Anti-ban sleep mode active.")
        return

    cl = Client()
    cl.set_user_agent() # Randomized Mobile Fingerprint

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        print(f"✅ Logged in as {BOT_USERNAME} (ID: {my_id})")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    processed_ids = set()
    if os.path.exists('processed.json'):
        with open('processed.json', 'r') as f:
            try: processed_ids = set(json.load(f))
            except: pass

    start_run = time.time()
    # GitHub Action run duration (approx 20 mins)
    while (time.time() - start_run) < 1200:
        for group_id in TARGET_GROUP_IDS:
            try:
                print(f"🔍 Scanning GC for new interactions...")
                thread = cl.direct_thread(group_id, amount=7)
                messages = thread.messages 
                
                for msg in reversed(messages):
                    if msg.id in processed_ids:
                        continue
                    
                    # Don't reply to self
                    if str(msg.user_id) == my_id:
                        processed_ids.add(msg.id)
                        continue

                    text = (msg.text or "").lower()
                    
                    # DETECTION LOGIC
                    is_mentioned = f"@{BOT_USERNAME}".lower() in text
                    is_reply_to_me = False
                    
                    if hasattr(msg, 'reply_to_message') and msg.reply_to_message:
                        if str(msg.reply_to_message.user_id) == my_id:
                            is_reply_to_me = True

                    if is_mentioned or is_reply_to_me:
                        print(f"🎯 Found trigger! Mention: {is_mentioned} | Reply: {is_reply_to_me}")
                        
                        # Step 1: Human Reading Delay
                        time.sleep(random.uniform(5, 12))
                        
                        sender = "Friend"
                        try:
                            sender = cl.user_info_v1(msg.user_id).username
                        except: pass
                        
                        ai_response = get_ai_reply(text, sender)
                        
                        if ai_response:
                            # Step 2: Typing Simulation Delay
                            typing_delay = len(ai_response) * 0.15 + random.uniform(3, 6)
                            print(f"⌨️ Typing response to {sender} for {typing_delay:.1f}s...")
                            time.sleep(min(typing_delay, 15))
                            
                            # Step 3: Send Reply
                            cl.direct_send(ai_response, thread_ids=[group_id], reply_to_message_id=msg.id)
                            print(f"✅ Successfully replied to {sender}")
                    
                    processed_ids.add(msg.id)

            except Exception as e:
                print(f"⚠️ Warning: {e}")
                if "429" in str(e):
                    print("🚨 Rate Limit Hit. Sleeping for 20 mins.")
                    return

        # Progress Persistence
        with open('processed.json', 'w') as f:
            json.dump(list(processed_ids)[-100:], f)
            
        # Random Gap between scanning cycles
        sleep_gap = random.randint(60, 150)
        print(f"☕ Taking a break for {sleep_gap}s...")
        time.sleep(sleep_gap)

if __name__ == "__main__":
    run_bot()
