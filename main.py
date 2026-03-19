import telebot
import requests
from telebot import types
import time
import urllib.parse
from threading import Thread
from flask import Flask
import os

# --- KEEP ALIVE SERVER (RENDER UCHUN) ---
# Bu qism botni "uyg'oq" saqlash uchun kichik veb-server vazifasini bajaradi
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render odatda 8080 yoki 10000 portni ishlatadi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # Asosiy dastur bilan birga yopilishi uchun
    t.start()

# --- СОЗЛАМАЛАР ---
# O'zingizning ma'lumotlaringizni shu yerga qo'ying
BOT_TOKEN = "BU_YERGA_TELEGRAM_TOKEN_QOYING"
FOOTBALL_API_KEY = "BU_YERGA_FOOTBALL_API_KEY_QOYING"
ADMIN_ID = 7748146680 

bot = telebot.TeleBot(BOT_TOKEN)

# --- ФУНКЦИЯЛАР ---

def save_user_and_notify(message):
    user_id = str(message.chat.id)
    try:
        # Render'da fayllar vaqtinchalik bo'lishi mumkin, 
        # lekin kichik ro'yxat uchun ishlaydi
        with open("users_list.txt", "a+") as file:
            file.seek(0)
            users = file.read().splitlines()
            if user_id not in users:
                file.write(user_id + "\n")
    except:
        pass

def get_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get('matches', [])

        if not matches:
            return "📅 Бугунги кун учун муҳим ўйинлар топилмади."

        text = "📅 **БУГУНГИ ТОП-10 ЎЙИН**\n*(Тошкент вақти билан)*\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        for m in matches[:10]:
            home = m['homeTeam']['shortName'] or m['homeTeam']['name']
            away = m['awayTeam']['shortName'] or m['awayTeam']['name']
            utc_hour = int(m['utcDate'][11:13])
            minutes = m['utcDate'][14:16]
            uzb_hour = (utc_hour + 5) % 24
            time_str = f"{uzb_hour:02}:{minutes}"
            text += f"⏰ {time_str} | ⚽️ **{home}** — **{away}**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        return text
    except:
        return "❌ Маълумот олишда хатолик юз берди."

def get_europe_table(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        standings = data['standings'][0]['table']
        league_name = data['competition']['name']
        text = f"🏆 **{league_name}**\n\n"
        for team in standings[:15]:
            pos = team['position']
            name = team['team']['shortName'] or team['team']['name']
            pts = team['points']
            emoji = "✅" if league_code == "CL" and pos <= 8 else "•"
            text += f"{pos}. {emoji} {name} — {pts} очко\n"
        text += "\n🔄 *Маълумотлар реал вақтда янгиланади.*"
        return text
    except:
        return "❌ Жадвални юклашда хатолик юз берди."

# --- БОТ БУЙРУҚЛАРИ ---

@bot.message_handler(commands=['start'])
def welcome(message):
    save_user_and_notify(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Жадваллар", "📅 Ўйинлар куни")
    markup.add("📺 Ўйинни кўриш", "🔴 LIVE")
    markup.add("🏆 Жаҳон Чемпионати", "🎬 Видео шарҳлар")
    markup.add("📰 Янгиликлар")
    bot.send_message(message.chat.id, "⚽️ Футбол оламига хуш келибсиз!", reply_markup=markup)

@bot.message_handler(commands=['stat'])
def show_stat(message):
    if message.chat.id == ADMIN_ID:
        try:
            if os.path.exists("users_list.txt"):
                with open("users_list.txt", "r") as file:
                    count = len(set(file.read().splitlines()))
                bot.send_message(message.chat.id, f"📊 Статистика: {count} та обуначи.")
            else:
                bot.send_message(message.chat.id, "📊 База ҳали яратилмаган.")
        except:
            bot.send_message(message.chat.id, "📊 Хатолик юз берди.")

@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.text == "📰 Янгиликлар":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(
            types.InlineKeyboardButton(text="🇺🇿 Championat.asia", url="https://championat.asia/uz"),
            types.InlineKeyboardButton(text="⚽️ Tribuna.uz", url="https://kun.uz/news/category/sport"),
            types.InlineKeyboardButton(text="📈 Sports.uz", url="https://sports.uz/")
        )
        bot.send_message(message.chat.id, "📰 **Янгиликлар манбасини танланг:**", reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "🔴 LIVE":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(text="🌐 Жонли натижалар", web_app=types.WebAppInfo(url="https://www.livescore.com/en/")))
        bot.send_message(message.chat.id, "🔴 Жонли натижалар:", reply_markup=m)

    elif message.text == "📺 Ўйинни кўриш":
        markup = types.InlineKeyboardMarkup(row_width=1)
        search_query = "m.football.tv футбол live трансляция сегодня"
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        btn_google_live = types.InlineKeyboardButton(text="⚽️ Футбол LIVE (Google орқали)", url=google_url)
        share_text = "⚽️ Дўстим, мана бу ботда футболни жонли кўриш мумкин: https://t.me/Fudbolgamebot"
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_text)}"
        markup.add(btn_google_live, types.InlineKeyboardButton(text="🚀 Дўстларга юбориш", url=share_url))
        bot.send_message(message.chat.id, "📺 **Жонли эфирлар:**", reply_markup=markup, parse_mode="Markdown")

    elif message.text == "📅 Ўйинлар куни":
        wait_msg = bot.send_message(message.chat.id, "⌛️ Юкланмоқда...")
        bot.send_message(message.chat.id, get_matches(), parse_mode="Markdown")
        bot.delete_message(message.chat.id, wait_msg.message_id)

    elif message.text == "📊 Жадваллар":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ", "🇪🇸 Ла Лига", "🇮🇹 Серия А")
        markup.add("🇩🇪 Бундеслига", "🇪🇺 ЕЧЛ", "⬅️ Орқага")
        bot.send_message(message.chat.id, "Лигани танланг:", reply_markup=markup)

    elif message.text in ["🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ", "🇪🇸 Ла Лига", "🇮🇹 Серия А", "🇩🇪 Бундеслига", "🇪🇺 ЕЧЛ"]:
        codes = {"🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": "PL", "🇪🇸 Ла Лига": "PD", "🇮🇹 Серия А": "SA", "🇩🇪 Бундеслига": "BL1", "🇪🇺 ЕЧЛ": "CL"}
        wait_msg = bot.send_message(message.chat.id, "⌛️ Юкланмоқда...")
        bot.send_message(message.chat.id, get_europe_table(codes[message.text]), parse_mode="Markdown")
        bot.delete_message(message.chat.id, wait_msg.message_id)

    elif message.text == "⬅️ Орқага":
        welcome(message)

# --- ИШГА ТУШИРИШ ---
if __name__ == "__main__":
    keep_alive() # Veb-serverni ishga tushirish
    print("Bot ishga tushdi...")
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Xatolik: {e}")
            time.sleep(5)

