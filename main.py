import telebot
import requests
from bs4 import BeautifulSoup
import re
import os

# Проверяем переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SITE_LOGIN = os.environ.get('SITE_LOGIN') 
SITE_PASSWORD = os.environ.get('SITE_PASSWORD')

print(f"🔧 Проверка переменных...")
print(f"BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ Отсутствует'}")
print(f"SITE_LOGIN: {'✅ Установлен' if SITE_LOGIN else '❌ Отсутствует'}")
print(f"SITE_PASSWORD: {'✅ Установлен' if SITE_PASSWORD else '❌ Отсутствует'}")

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не установлен!")
    exit(1)

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

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
        if not SITE_LOGIN or not SITE_PASSWORD:
            return False
            
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
    if not SITE_LOGIN or not SITE_PASSWORD:
        bot.send_message(message.chat.id, "❌ Данные для авторизации не настроены")
        return
        
    bot.send_message(message.chat.id, "🔐 Пытаюсь авторизоваться...")
    if auth():
        bot.send_message(message.chat.id, "✅ Бот авторизован! Отправляй ссылку на тест с Решу ОГЭ")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка авторизации. Проверь логин/пароль")

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

if __name__ == "__main__":
    print("🔄 Бот запускается на Render...")
    bot.polling(none_stop=True, timeout=60)
