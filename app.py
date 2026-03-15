import telebot
import google.generativeai as genai
from flask import Flask, request
import time
import os

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8322781813:AAGeIw9Ydv4gJpDXNwyBVzOs8KUP3coUXJE"
GEMINI_API_KEY = "AIzaSyDkhCQCXbIzef97D2ZxvmRGBO5FmpUnDEk"

# قائمة الأدمنز
ADMIN_IDS = [2063443733, 7916847464, 8340080113, 7525164718, 1098659585, 
             8037286737, 7747494028, 5827144797, 8392588438, 8308080287, 
             7435636715, 5246436287, 6336899987, 7945419060, 7751207147, 
             7604695687, 5355388850, 7935579780, 6924192775, 7035480386, 
             7768210536]

BAD_WORDS = ["كس", "عرص", "شرموط", "قحبة", "منيوك", "نيج", "مص", "ز*ب", "اير"]

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text if message.text else ""

    # 1. نظام الكلمات الممنوعة (للأعضاء)
    if any(word in text for word in BAD_WORDS) and uid not in ADMIN_IDS:
        try:
            bot.delete_message(cid, message.message_id)
            bot.send_message(cid, "⚠️ التزم بآداب الحديث يا غالي!")
        except: pass
        return

    # 2. إذا عضو (مو أدمن) عمل ريبلاي على البوت
    if message.reply_to_message and message.reply_to_message.from_user.is_bot and uid not in ADMIN_IDS:
        # هون البوت رح يطنش الكلام تماماً، بس رح يتفاعل بإيموجي
        try:
            # تحليل النص لاختيار إيموجي مناسب
            if any(word in text for word in ["شكرا", "يسلمو", "كفو", "ورده"]):
                bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji("❤️")], is_big=False)
            elif any(word in text for word in ["هههه", "😂", "مضحك"]):
                bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji("😂")], is_big=False)
            else:
                bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji("👍")], is_big=False)
        except: pass
        return

    # 3. إذا الأدمن كتب "مهندسنا" (بدون ريبلاي)
    if "مهندسنا" in text and uid in ADMIN_IDS and not message.reply_to_message:
        prompt = f"أنت المهندس X، مبرمجك عدنان (20 سنة، مهندس وباريستا). رد بلهجة شامية وتواضع على الأدمن {message.from_user.first_name}."
        try:
            response = ai_model.generate_content(prompt)
            bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, "مخي علّق شوي، جرب مرة تانية 😅")
        return

    # 4. ميزة "مهندسنا جاوب" (الأدمن بيخلي البوت يرد على عضو)
    if text == "مهندسنا جاوب" and uid in ADMIN_IDS and message.reply_to_message:
        target_msg = message.reply_to_message
        user_name = target_msg.from_user.first_name
        user_question = target_msg.text if target_msg.text else "هذه الرسالة"
        
        waiting_msg = bot.reply_to(target_msg, "تكرم يا هندسة، عم فكر بالرد... 🧠")
        
        try:
            prompt = f"أنت المهندس X. الأدمن طلب منك ترد على العضو {user_name} اللي سأل: {user_question}. جاوبه بلهجة شامية مبسطة جداً ومفيدة."
            response = ai_model.generate_content(prompt)
            bot.edit_message_text(response.text, cid, waiting_msg.message_id)
        except:
            bot.edit_message_text("والله يا غالي حاولت جاوبه بس مخي علّق 😅", cid, waiting_msg.message_id)
        return

    # 5. أوامر الإدارة (عنوم، حظر)
    if uid in ADMIN_IDS and message.reply_to_message:
        if text == "عنوم":
            bot.restrict_chat_member(cid, message.reply_to_message.from_user.id, until_date=int(time.time() + 3600))
            bot.reply_to(message, "✅ تم الكتم ساعة بنجاح 😴")
        elif text == "حظر":
            bot.kick_chat_member(cid, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ تم الحظر بنجاح 👋")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "المهندس X شغال وبأفضل حال! 😎", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
