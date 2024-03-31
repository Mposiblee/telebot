import telebot
from telebot import types
import psycopg2
import pandas as pd
from time import sleep
import requests

DATABASE = 'your_database_name'
TOKEN = 'token bot'
bot = telebot.TeleBot(TOKEN)

DATABASE = 'postgres'
USER = 'postgres'
PASSWORD = 'your password'
HOST = 'localhost'

conn = psycopg2.connect(dbname=DATABASE, user=USER, password=PASSWORD, host=HOST)

STATE_NONE = 0
STATE_AWAITING_FIO = 1

def polling_with_backoff(bot):
    backoff_time = 1 
    max_backoff_time = 60 

    while True:
        try:
            bot.polling(none_stop=True)
            backoff_time = 1
        except requests.exceptions.ReadTimeout:
            print(f"Ошибка времени ожидания. Повторная попытка через {backoff_time} секунд...")
            sleep(backoff_time)
            backoff_time *= 2 
            if backoff_time > max_backoff_time:
                backoff_time = max_backoff_time
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            sleep(10)  


@bot.message_handler(commands=['send_data'])
def send_data(message):
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM user_data;')
            rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=['user_id', 'fio', 'number'])

        file_path = r'F:\your_location\user_data.xlsx'
        df.to_excel(file_path, index=False, engine='openpyxl')

        with open(file_path, 'rb') as file:
            bot.send_document(message.chat.id, file)

    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при обработке вашего запроса.")
        print("Ошибка:", e)

@bot.message_handler(commands=['send_data'])
def send_data(message):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM user_data;')
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=['user_id', 'fio', 'number'])

    file_path = 'F:\\projects\\bot_random\\user_data.xlsx'
    df.to_excel(file_path, index=False, engine='openpyxl')

    with open(file_path, 'rb') as file:
        bot.send_document(message.chat.id, file)

def get_user_state(user_id):
    with conn.cursor() as cur:
        cur.execute('SELECT state FROM user_states WHERE user_id = %s', (user_id,))
        result = cur.fetchone()
        return result[0] if result else STATE_NONE

def update_user_state(user_id, state):
    with conn.cursor() as cur:
        cur.execute('INSERT INTO user_states (user_id, state) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET state = EXCLUDED.state', (user_id, state))
        conn.commit()

def get_next_number():
    with conn.cursor() as cur:
        cur.execute('SELECT MAX(number) FROM user_data')
        result = cur.fetchone()
        return result[0] + 1 if result and result[0] else 1

@bot.message_handler(commands=['start'])
def start_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    number_button = types.KeyboardButton('Получить номер')
    my_number_button = types.KeyboardButton('Мой номер')
    markup.row(number_button, my_number_button)
    bot.send_message(message.chat.id, "Нажмите на кнопку ПОЛУЧИТЬ НОМЕР, чтобы участвовать в розыгрыше\n\nby @mposible", reply_markup=markup)
    update_user_state(message.from_user.id, STATE_NONE)

@bot.message_handler(func=lambda message: message.text == "Получить номер")
def request_fio(message):
    bot.send_message(message.chat.id, "Введите ваше ФИО, пожалуйста:")
    update_user_state(message.from_user.id, STATE_AWAITING_FIO)

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == STATE_AWAITING_FIO)
def give_number(message):
    user_id = message.from_user.id
    fio = message.text
    number = get_next_number() 

    with conn.cursor() as cur:
        cur.execute('SELECT number FROM user_data WHERE user_id = %s', (user_id,))
        result = cur.fetchone()

    if result:
        bot.send_message(message.chat.id, "Вы уже получили номер")
    else:
        if number <= 10000:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO user_data (user_id, fio, number) VALUES (%s, %s, %s)', (user_id, fio, number))
                conn.commit()
            bot.send_message(message.chat.id, f"Ваш номер: {number}. Спасибо за регистрацию, {fio}!")
        else:
            bot.send_message(message.chat.id, "Извините, все номера уже выданы")

    update_user_state(user_id, STATE_NONE)
@bot.message_handler(func=lambda message: message.text == "Мой номер")
def show_my_number(message):
    user_id = message.from_user.id

    with conn.cursor() as cur:
        cur.execute('SELECT number FROM user_data WHERE user_id = %s', (user_id,))
        result = cur.fetchone()
        
    if result:
        number = result[0]
        bot.send_message(message.chat.id, f"Ваш номер: {number}.")
    else:
        bot.send_message(message.chat.id, "Вы еще не получили номер")


polling_with_backoff(bot)