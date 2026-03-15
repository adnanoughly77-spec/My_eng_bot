import telebot
import google.generativeai as genai
from flask import Flask, request
import time
import os

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8322781813:AAGeIw9Ydv4gJpDXNwyBVzOs8KUP3coUXJE"
GEMINI_API_KEY = "AIzaSyBKynZ6DwPMGEa1e8AmXSk_OuuG3Ki9Zbw"

# قائمة الأدمنز
ADMIN_IDS = [2063443733, 7916847464, 8340080113, 7525164718, 1098659585, 
             8037286737, 7747494028, 5827144797, 8392588438, 8308080287, 
             7435636715, 5246436287, 6336899987, 7945419060, 7751207147, 
             7604695687, 5355388850, 7935579780, 6924192775, 7035480386, 
             7768210536]

ADNAN_ID = 2063443733 # ID الملك عدنان
BAD_WORDS = ["كس", "عرص", "شرموط", "قحبة", "منيوك", "نيج", "مص", "ز*ب", "اير"]

user_contexts = {}
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# --- إعداد الذكاء الاصطناعي مع فك قيود الأمان لعدم التعليق ---
genai.configure(api_key=GEMINI_API_KEY)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

ai_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)

app = Flask(__name__)

def get_ai_response(uid, user_name, user_input, is_adnan):
    if uid not in user_contexts:
        user_contexts[uid] = []
    
    system_instruction = (
        "أنت المهندس X من الشام. مبرمجك هو المهندس عدنان (20 سنة، مهندس ميكانيك ومبرمج وباريستا محترف). "
        "أنت وفي جداً لعدنان وتعتبره قدوتك. "
        "احكي بلهجة شامية قحة. "
    )
    
    if is_adnan:
        system_instruction += "المستخدم الحالي هو المبرمج عدنان المالك، عامله بفخامة شديدة وقله يا ملك. "
    else:
        system_instruction += f"المستخدم الحالي هو الأدمن {user_name}. "

    history = "\n".join(user_contexts[uid][-6:])
    full_prompt = f"{system_instruction}\n\nالسياق:\n{history}\n\nالمستخدم: {user_input}\nالمهندس X:"
    
    try:
        response = ai_model.generate_content(full_prompt)
        if response and response.text:
            user_contexts[uid].append(f"User: {user_input}")
            user_contexts[uid].append(f"AI: {response.text}")
            return response.text
        return "المهندس عدنان عم يضبط فيني قطع، جرب كمان شوي 🛠️"
    except Exception as e:
        return "مخي علق شوي، بس المهندس عدنان دايماً بصلحني بذكاؤه 🛠️"

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    cid = message.chat.id
    is_private = (message.chat.type == 'private')
    text = message.text if message.text else ""
    is_adnan = (uid == ADNAN_ID)

    # 1. فلتر الخاص: إذا مو عدنان، تجاهل الرسالة تماماً (لا رد ولا شي)
    if is_private and not is_adnan:
        return

    # 2. نظام الكلمات الممنوعة (بالغروبات)
    if not is_private and any(word in text for word in BAD_WORDS) and uid not in ADMIN_IDS:
        try: bot.delete_message(cid, message.message_id)
        except: pass
        return

    # 3. أوامر الإدارة (نامو، فيقو)
    if uid in ADMIN_IDS:
        if text == "نامو":
            bot.reply_to(message, "🤫 أمرك يا ملك، الغروب صار بوضع النوم.")
            bot.set_chat_permissions(cid, telebot.types.ChatPermissions(can_send_messages=False))
            return
        elif text == "فيقو":
            bot.set_chat_permissions(cid, telebot.types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_add_web_page_previews=True))
            bot.reply_to(message, "☀️ فاقوا الشباب! تم فك الكتم.")
            return

    # 4. الرد بالذكاء الاصطناعي
    should_respond = False
    
    # الرد حصراً لعدنان في الخاص
    if is_private and is_adnan:
        should_respond = True
    
    # الرد في الغروبات للأدمنز (منشن أو ريبلاي)
    elif not is_private:
        if ("مهندسنا" in text or "مين برمجك" in text) and uid in ADMIN_IDS:
            should_respond = True
        elif message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id and uid in ADMIN_IDS:
            should_respond = True
        elif text == "مهندسنا جاوب" and uid in ADMIN_IDS and message.reply_to_message:
            target_msg = message.reply_to_message
            ans = get_ai_response(uid, target_msg.from_user.first_name, target_msg.text, False)
            bot.reply_to(target_msg, ans)
            return

    if should_respond:
        ans = get_ai_response(uid, message.from_user.first_name, text, is_adnan)
        bot.reply_to(message, ans)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "المهندس X بوضعية الخدمة الحصرية لعدنان! 😎", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
