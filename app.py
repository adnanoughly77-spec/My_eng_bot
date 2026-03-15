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

ADNAN_ID = 2063443733
BAD_WORDS = ["كس", "عرص", "شرموط", "قحبة", "منيوك", "نيج", "مص", "ز*ب", "اير"]

# قاموس الذاكرة المنفصلة
user_contexts = {}

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

def get_ai_response(uid, user_name, user_input, is_adnan):
    if uid not in user_contexts:
        user_contexts[uid] = []
    
    # تعليمات الشخصية والولاء لعدنان
    base_prompt = (
        "أنت المهندس X من الشام، مبرمجك هو المهندس عدنان (20 سنة، مهندس ميكانيك ومبرمج وباريستا محترف). "
        "إذا حدا سألك مين برمجك، قلهم: 'المهندس عدنان هو اللي برمجني'. "
        "وإذا سألوك كيف، قلهم: 'برمجني بلغة البايثون (Python) وتعب فيني كتير وسهر ليالي لحتى صرت بهذا الذكاء'. "
        "احكي بلهجة شامية، وتواضع مع الأدمنز، وبسط العلوم الصعبة. "
    )
    
    if is_adnan:
        base_prompt += "المستخدم الحالي هو عدنان المالك ومبرمجي، عامله بفخامة شديدة وقله يا ملك أو يا سيدي. "
    else:
        base_prompt += f"المستخدم الحالي هو الأدمن {user_name}. إذا عرف عن حاله، احفظ معلوماته وعامله على أساسها دائماً ولا تخلط مواضيعه مع غيره. "

    context_history = "\n".join(user_contexts[uid][-10:])
    full_prompt = f"{base_prompt}\nتاريخ المحادثة السابقة:\n{context_history}\n\nالمستخدم يقول: {user_input}"
    
    try:
        response = ai_model.generate_content(full_prompt)
        user_contexts[uid].append(f"User: {user_input}")
        user_contexts[uid].append(f"AI: {response.text}")
        return response.text
    except:
        return "مخي علق شوي، بس المهندس عدنان دايماً بصلحني بذكاؤه 🛠️"

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text if message.text else ""
    is_adnan = (uid == ADNAN_ID)

    # 1. فلتر الكلمات
    if any(word in text for word in BAD_WORDS) and uid not in ADMIN_IDS:
        try: bot.delete_message(cid, message.message_id)
        except: pass
        return

    # 2. أوامر الإدارة (نامو، فيقو)
    if uid in ADMIN_IDS:
        if text == "نامو":
            bot.reply_to(message, "🤫 أمرك يا ملك، الغروب صار بوضع النوم.")
            bot.set_chat_permissions(cid, telebot.types.ChatPermissions(can_send_messages=False))
            return
        elif text == "فيقو":
            bot.set_chat_permissions(cid, telebot.types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_add_web_page_previews=True))
            bot.reply_to(message, "☀️ فاقوا الشباب! نورتوا.")
            return

    # 3. شروط الرد بالذكاء الاصطناعي
    should_respond = False
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
        response_text = get_ai_response(uid, message.from_user.first_name, text, is_adnan)
        bot.reply_to(message, response_text)
    elif message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id and uid not in ADMIN_IDS:
        try: bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji("👍")], is_big=False)
        except: pass

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "المهندس X جاهز لخدمة المعلم عدنان! 😎", 200

# --- حل مشكلة البورت في Render ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
