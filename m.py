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
        res = r.json()
        return res['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

def run_bot():
    cl = Client()
    cl.set_user_agent()

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        print(f"✅ Login Successful! Bot User ID: {my_id}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_run = time.time()
    
    print(f"🚀 Bot Started at {datetime.now(IST)}. Monitoring Group: {TARGET_GROUP_IDS[0]}")

    while (time.time() - start_run) < 1200:
        for group_id in TARGET_GROUP_IDS:
            try:
                print(f"\n--- Scanning Messages ({datetime.now(IST).strftime('%H:%M:%S')}) ---")
                
                # Sabse latest 10 messages uthayega
                messages = cl.direct_messages(group_id, amount=10)
                
                if not messages:
                    print("⚠️ No messages found in this Group ID. Kya ID sahi hai?")

                for msg in reversed(messages):
                    # LOG HAR EK MESSAGE: Isse pata chalega bot kya dekh raha hai
                    sender_id = str(msg.user_id)
                    msg_text = msg.text or "[Non-text message]"
                    print(f"📩 [LOG] Msg from {sender_id}: {msg_text}")

                    if msg.id in processed_ids or sender_id == my_id:
                        continue
                    
                    text_lower = msg_text.lower()
                    
                    # Detection
                    is_mentioned = f"@{BOT_USERNAME}".lower() in text_lower
                    is_reply_to_me = False
                    if msg.reply_to_message and str(msg.reply_to_message.user_id) == my_id:
                        is_reply_to_me = True
                    
                    if is_mentioned or is_reply_to_me:
                        print(f"🎯 TRIGGER FOUND! Processing reply for: {msg_text}")
                        
                        # AI Reply Generation
                        reply = get_ai_reply(msg_text, "User")
                        
                        if reply:
                            print(f"🤖 AI Generated Reply: {reply}")
                            time.sleep(random.randint(5, 8))
                            cl.direct_send(reply, thread_ids=[group_id], reply_to_message_id=msg.id)
                            print(f"✅ Reply Sent Successfully to ID {msg.id}")
                        else:
                            print("❌ Failed to get AI reply.")
                    
                    processed_ids.add(msg.id)

            except Exception as e:
                print(f"⚠️ Loop Error: {e}")
        
        # Thoda lamba break taaki spam na lage
        wait_time = random.randint(60, 90)
        print(f"Waiting {wait_time}s for next scan...")
        time.sleep(wait_time)

if __name__ == "__main__":
    run_bot()
    
