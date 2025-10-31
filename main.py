import telebot
import requests
from bs4 import BeautifulSoup
import re
import flask
from threading import Thread

# Прямой токен
BOT_TOKEN = "8041110005:AAEyH4yY9ubOW8Wi4GUruoWsKrlVNMK_gqo"
SITE_LOGIN = "skolaotzyv@gmail.com"
SITE_PASSWORD = "ufZ-kJK-r5Z-bNW"

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Создаем Flask app для webhooks
app = flask.Flask(__name__)

SESSION = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
SESSION.headers.update(HEADERS)

LOGIN_DATA = {
    'login': SITE_LOGIN,
    'password': SITE_PASSWORD
}

def auth():
    try:
        login_url = "https://oge.sdamgia.ru/profile"
        auth_response = SESSION.post(login_url, data=LOGIN_DATA, headers=HEADERS)
        
        if auth_response.status_code == 200:
            profile_check = SESSION.get("https://oge.sdamgia.ru/profile", headers=HEADERS)
            if "войти" in profile_check.text.lower():
                return False
            return True
        return False
        
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔐 Пытаюсь авторизоваться...")
    if auth():
        bot.send_message(message.chat.id, "✅ Бот авторизован! Отправляй ссылку на тест с Решу ОГЭ")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка авторизации")

@bot.message_handler(func=lambda message: True)
def solve_test(message):
    try:
        url = message.text.strip()
        
        if not url.startswith('http'):
            bot.send_message(message.chat.id, "❌ Отправь корректную ссылку на тест")
            return
        
        bot.send_message(message.chat.id, "⏳ Анализирую тест...")
        
        response = SESSION.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        questions = soup.find_all('div', class_='question')
        
        if not questions:
            questions = soup.find_all('div', id=re.compile(r'question|task|problem'))
        
        if not questions:
            bot.send_message(message.chat.id, "❌ Не могу найти вопросы. Проверь ссылку")
            return
        
        answers = []
        for i, question in enumerate(questions):
            correct_answer = question.find('div', class_='right-answer')
            if correct_answer:
                answers.append(f"Вопрос {i+1}: {correct_answer.text.strip()}")
            else:
                answer_input = question.find('input', {'checked': True})
                if answer_input:
                    answers.append(f"Вопрос {i+1}: {answer_input.find_next('label').text.strip()}")
                else:
                    answers.append(f"Вопрос {i+1}: Ответ не найден")
        
        result = "\n".join(answers)
        
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for part in parts:
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, f"📊 Найдено ответов: {len(questions)}\n\n{result}")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# Webhook route для Render
@app.route('/')
def index():
    return "🤖 Бот работает!"

@app.route('/webhook/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

# Запускаем бота в отдельном потоке
def run_bot():
    print("🔄 Запуск бота...")
    try:
        # Удаляем webhook чтобы очистить предыдущие instances
        bot.remove_webhook()
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Ошибка polling: {e}")

if __name__ == "__main__":
    print("🚀 Starting server...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask app
    app.run(host='0.0.0.0', port=10000, debug=False)
