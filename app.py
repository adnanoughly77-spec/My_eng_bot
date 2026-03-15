import telebot
import google.generativeai as genai
from flask import Flask, request
import time
import os

# --- الإعدادات الأساسية (لا تعدلها) ---
BOT_TOKEN = "8322781813:AAGeIw9Ydv4gJpDXNwyBVzOs8KUP3coUXJE"
GEMINI_API_KEY = "AIzaSyDkhCQCXbIzef97D2ZxvmRGBO5FmpUnDEk"

ADMIN_IDS = [2063443733, 7916847464, 8340080113, 7525164718, 1098659585, 
             8037286737, 7747494028, 5827144797, 8392588438, 8308080287, 
             7435636715, 5246436287, 6336899987, 7945419060, 7751207147, 
             7604695687, 5355388850, 7935579780, 6924192775, 7035480386, 
             7768210536]

OWNER_ID = 2063443733 
BAD_WORDS = ["كس", "عرص", "شرموط", "قحبة", "منيوك", "نيج", "مص", "ز*ب", "اير"]
global_mute_until = 0

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

def check_weather_response(text):
    t = text.lower()
    if any(word in t for word in ["شوب", "حر", "نار", "فطس"]):
        return "والله الجو نار، بس عصير عدنان بيعالج الحر ويروق الأعصاب 🍹"
    if any(word in t for word in ["برد", "شتا", "مطر", "تليج"]):
        return "جو الشتا بالشام شي ثاني، بدها كاسة قهوة من تحت إيدين عدنان ☕"
    return None

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    global global_mute_until
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text if message.text else ""
    name = message.from_user.first_name

    # فلتر الكلمات (حذف + كتم)
    if any(word in text for word in BAD_WORDS) and uid not in ADMIN_IDS:
        try:
            bot.delete_message(cid, message.message_id)
            bot.restrict_chat_member(cid, uid, can_send_messages=False)
            bot.send_message(cid, f"🚫 تم كتم {name} كتم أبدي بسبب الكلمات الممنوعة.")
        except: pass
        return

    # ردود الطقس
    weather_reply = check_weather_response(text)
    if weather_reply:
        bot.reply_to(message, weather_reply)
        return

    # أوامر الأدمنز
    if uid in ADMIN_IDS:
        if text == "عنوم" and message.reply_to_message:
            bot.restrict_chat_member(cid, message.reply_to_message.from_user.id, can_send_messages=False, until_date=int(time.time() + 3600))
            bot.reply_to(message, "✅ تم الإرسال إلى النوم ساعة 😴")
            return
        if text == "حظر" and message.reply_to_message:
            bot.kick_chat_member(cid, message.reply_to_message.from_user.id)
            bot.reply_to(message, "👋 تم الحظر بنجاح.")
            return
        if text == "نامو":
            global_mute_until = time.time() + 900
            bot.reply_to(message, "🔇 كتم عام 15 دقيقة ☕")
            return

    # ذكاء اصطناعي
    if text.startswith("مهندسنا"):
        question = text.replace("مهندسنا", "").strip()
        if question:
            msg = bot.reply_to(message, "جاري التفكير... 🧠")
            try:
                response = ai_model.generate_content(f"أنت المهندس X، مبرمجك عدنان (عمره 20، مهندس وباريستا). رد بلهجة شاميّة وتواضع: {question}")
                bot.edit_message_text(response.text, cid, msg.message_id)
            except:
                bot.edit_message_text("صار عندي تعليق بسيط، جرب مرة تانية 😅", cid, msg.message_id)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "البوت شغال وعم ينتظر الأوامر! 😎", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
