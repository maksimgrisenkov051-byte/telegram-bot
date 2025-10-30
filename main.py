import telebot
import requests
from bs4 import BeautifulSoup
import re
import os

# Используем токен из переменных окружения
bot = telebot.TeleBot(os.environ.get('8041110005:AAEyH4yY9ubOW8Wi4GUruoWsKrlVNMK_gqo'))

SESSION = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
SESSION.headers.update(HEADERS)

# Данные из переменных окружения
LOGIN_DATA = {
    'login': os.environ.get('skolaotzyv@gmail.com'),
    'password': os.environ.get('ufZ-kJK-r5Z-bNW')
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
                answers.append(f"Вопрос {i + 1}: {correct_answer.text.strip()}")
            else:
                answer_input = question.find('input', {'checked': True})
                if answer_input:
                    answers.append(f"Вопрос {i + 1}: {answer_input.find_next('label').text.strip()}")
                else:
                    answers.append(f"Вопрос {i + 1}: Ответ не найден")

        result = "\n".join(answers)

        if len(result) > 4000:
            parts = [result[i:i + 4000] for i in range(0, len(result), 4000)]
            for part in parts:
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, f"📊 Найдено ответов: {len(questions)}\n\n{result}")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    print("🔄 Бот запускается на Render...")
    bot.polling(none_stop=True, timeout=60)