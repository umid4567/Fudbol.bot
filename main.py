import telebot
import requests
from telebot import types
import time
import urllib.parse
from threading import Thread
from flask import Flask
import os

# --- 1. RENDER UCHUN VEB-SAYT ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot holati: Faol ✅. Avto-gollar tizimi yoqilgan."

def run():
    # Render uchun portni sozlash
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. SOZLAMALAR ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")
ADMIN_ID = 7748146680 

bot = telebot.TeleBot(BOT_TOKEN)
last_sent_video = "" 

# --- 3. FUNKSIYALAR ---

def save_user_and_notify(message):
    user_id = str(message.chat.id)
    try:
        if not os.path.exists("users_list.txt"):
            open("users_list.txt", "w").close()
        with open("users_list.txt", "a+") as file:
            file.seek(0)
            users = file.read().splitlines()
            if user_id not in users:
                file.write(user_id + "\n")
    except:
        pass

def auto_broadcast_goals():
    global last_sent_video
    while True:
        try:
            response = requests.get("https://www.scorebat.com/video-api/v3/")
            data = response.json()
            matches = data.get('response', [])

            if matches:
                latest = matches[0]
                title = latest['title']
                url = latest['matchviewUrl']

                if title != last_sent_video:
                    last_sent_video = title
                    if os.path.exists("users_list.txt"):
                        with open("users_list.txt", "r") as f:
                            users = set(f.read().splitlines())
                        
                        caption = f"⚽️ **ЯНГИ ГОЛ!**\n\n🎬 {title}\n\nКўриш учун пастдаги тугмани босинг 👇"
                        m = types.InlineKeyboardMarkup()
                        m.add(types.InlineKeyboardButton(text="🎬 Видеони кўриш", web_app=types.WebAppInfo(url=url)))

                        for user in users:
                            try:
                                bot.send_message(user, caption, reply_markup=m, parse_mode="Markdown")
                                time.sleep(0.2)
                            except:
                                continue
            time.sleep(900)
        except:
            time.sleep(60)

def get_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get('matches', [])
        if not matches: return "📅 Бугунги кун учун муҳим ўйинлар топилмади."
        text = "📅 **БУГУНГИ ТОП-10 ЎЙИН**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        for m in matches[:10]:
            home = m['homeTeam']['shortName'] or m['homeTeam']['name']
            away = m['awayTeam']['shortName'] or m['awayTeam']['name']
            utc_hour = int(m['utcDate'][11:13])
            uzb_hour = (utc_hour + 5) % 24
            time_str = f"{uzb_hour:02}:{m['utcDate'][14:16]}"
            text += f"⏰ {time_str} | ⚽️ **{home}** — **{away}**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        return text
    except: return "❌ Маълумот олишда хатолик юз берди."

def get_europe_table(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'standings' not in data or not data['standings']:
            return "⚠️ Ҳозирча жадвал маълумотлари йўқ."
        standings = data['standings'][0]['table']
        league_name = data['competition']['name']
        text = f"🏆 **{league_name}**\n\n"
        for team in standings[:15]:
            pos = team['position']
            name = team['team']['shortName'] or team['team']['name']
            pts = team['points']
            text += f"{pos}. {name} — {pts} очко\n"
        return text
    except Exception as e:
        return "❌ Жадвални юклашда хатолик юз берди."

# --- 4. BOT BUYRUQLARI ---

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
        if os.path.exists("users_list.txt"):
            with open("users_list.txt", "r") as file:
                count = len(set(file.read().splitlines()))
            bot.send_message(message.chat.id, f"📊 Статистика: {count} та обуначи.")
        else:
            bot.send_message(message.chat.id, "📊 База бўш.")

@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.text == "📰 Янгиликлар":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(
            types.InlineKeyboardButton(text="🇺🇿 Championat.asia", url="https://championat.asia/uz"),
            types.InlineKeyboardButton(text="⚽️ Tribuna.uz", url="https://kun.uz/news/category/sport"),
            types.InlineKeyboardButton(text="📈 Sports.uz", url="https://sports.uz/")
        )
        bot.send_message(message.chat.id, "📰 **Манбани танланг:**", reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "🔴 LIVE":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(text="🌐 Жонли натижалар", web_app=types.WebAppInfo(url="https://www.livescore.com/en/")))
        bot.send_message(message.chat.id, "🔴 LIVE натижалар:", reply_markup=m)

    elif message.text == "📺 Ўйинни кўриш":
        markup = types.InlineKeyboardMarkup(row_width=1)
        stream_url = "https://m.futboll.tv/tv.php"
        markup.add(types.InlineKeyboardButton(text="⚽️ Эфирга кириш", web_app=types.WebAppInfo(url=stream_url)))
        bot.send_message(message.chat.id, "📺 **Жонли эфир маркази:**", reply_markup=markup, parse_mode="Markdown")

    elif message.text == "📅 Ўйинлар куни":
        bot.send_message(message.chat.id, get_matches(), parse_mode="Markdown")

    elif message.text == "🏆 Жаҳон Чемпионати":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(text="🏆 Жадвални кўриш", url="https://www.flashscore.com/football/world/world-cup/standings/"))
        bot.send_message(message.chat.id, "🏆 ЖЧ-2026 саралаши ва жадвали:", reply_markup=m)

    elif message.text == "🎬 Видео шарҳлар":
        query = "football highlights today"
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(text="🎬 YouTube-да кўриш", url=search_url))
        bot.send_message(message.chat.id, "🎬 Энг янги футбол шарҳлари:", reply_markup=m)

    elif message.text == "📊 Жадваллар":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ", "🇪🇸 Ла Лига", "🇮🇹 Серия А")
        markup.add("🇩🇪 Бундеслига", "🇪🇺 ЕЧЛ", "⬅️ Орқага")
        bot.send_message(message.chat.id, "Лигани танланг:", reply_markup=markup)

    elif message.text in ["🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ", "🇪🇸 Ла Лига", "🇮🇹 Серия А", "🇩🇪 Бундеслига", "🇪🇺 ЕЧЛ"]:
        wait_msg = bot.send_message(message.chat.id, "⌛️ Маълумот юкланмоқда...")
        codes = {"🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": "PL", "🇪🇸 Ла Лига": "PD", "🇮🇹 Серия А": "SA", "🇩🇪 Бундеслига": "BL1", "🇪🇺 ЕЧЛ": "CL"}
        league_code = codes.get(message.text)
        table_text = get_europe_table(league_code)
        bot.send_message(message.chat.id, table_text, parse_mode="Markdown")
        bot.delete_message(message.chat.id, wait_msg.message_id)

    elif message.text == "⬅️ Орқага":
        welcome(message)

# --- 5. ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive() 
    Thread(target=auto_broadcast_goals).start()
    print("Bot va Avto-gollar tizimi ishga tushdi...")
    bot.infinity_polling(timeout=20)

