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

def get_ai_reply(user_message, username, context_message=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # AI ko batana ki ye swipe reply hai
    system_content = f"You are @{BOT_USERNAME}, a witty Indian girl. You just got a reply to your message. Be savage and short (max 10 words)."
    user_content = f"User {username} replied to your message '{context_message}': {user_message}" if context_message else f"User {username}: {user_message}"

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
    # Desktop User-Agent swipe data fetch karne mein zyada help karta hai
    cl.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = str(cl.user_id)
        log(f"✅ Bot Online! ID: {my_id}")
    except Exception as e:
        log(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    start_time = time.time()
    
    while (time.time() - start_time) < 1320:
        try:
            log(f"--- Scanning Deep Metadata ---")
            # thread_v2 use karne se swipe information zyada milti hai
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

                # --- 🎯 THE SWIPE FIX (DEEP SCAN) ---
                # Instagram API mein swipe data 'reply_to_item' ya 'replied_to_message' mein hota hai
                try:
                    # Method A: Object Attribute check
                    if hasattr(msg, 'replied_to_message') and msg.replied_to_message:
                        r_msg = msg.replied_to_message
                        if str(getattr(r_msg, 'user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = getattr(r_msg, 'text', 'Previous Message')
                    
                    # Method B: Dictionary check (for different library versions)
                    if not is_reply_to_me:
                        m_dict = msg.dict() if hasattr(msg, 'dict') else {}
                        reply_info = m_dict.get('replied_to_message') or m_dict.get('reply_to_item')
                        if reply_info and str(reply_info.get('user_id', '')) == my_id:
                            is_reply_to_me = True
                            context_text = reply_info.get('text', 'Previous Message')
                except: pass

                log(f"📩 [{text[:15]}] | Swipe: {is_reply_to_me} | Mention: {is_mentioned}")

                if is_mentioned or is_reply_to_me:
                    log("🎯 Target Found! Replying...")
                    sender = "User"
                    try: sender = cl.user_info_v1(msg.user_id).username
                    except: pass
                    
                    reply_content = get_ai_reply(text, sender, context_text)
                    if reply_content:
                        time.sleep(random.randint(2, 5))
                        # Multi-Method Reply Engine (No crashes)
                        try:
                            # Try to reply as a thread (swipe back)
                            cl.direct_answer(reply_content, TARGET_GROUP_ID, msg.id)
                            log(f"✅ Replied to Swipe!")
                        except:
                            cl.direct_send(reply_content, thread_ids=[TARGET_GROUP_ID])
                            log(f"✅ Fallback Sent!")
                
                processed_ids.add(msg.id)

        except Exception as e:
            log(f"⚠️ Loop Warning: {e}")
            time.sleep(10)
        
        time.sleep(30)

if __name__ == "__main__":
    run_bot()
    
