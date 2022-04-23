from flask import Flask
from flask import request

import time 
import telebot
import os
import psycopg2

DB_URL = os.environ.get('DATABASE_URL', None)
TOKEN = os.environ.get('TOKEN', None)

# conn = psycopg2.connect(dbname='database', user='db_user', 
#                         password='mypassword', host=DB_URL)
# cursor = conn.cursor()

bot = telebot.TeleBot(TOKEN)

subscriptions_all = []

def make_measures_message(data):
    retval = None
    retval = 'Получены показания от логгера\n' + \
        f'Серийный номер: {data["serial_number"]}\n' + \
        f'MAC: {data["ap_mac"]}\n' + \
        f'Версия HW: {data["hw_version"]}\n' + \
        f'Версия SW {data["fw_version"]}\n'
    for d in data["measures"]:
        retval += f'Время: {time.ctime(d["timestamp"])}  Температура: {d["value"]}°C\n'
    print(retval)
    return retval

def make_button_message(data):
    retval = None
    retval = 'Была нажата кнопка\n' + \
        f'Серийный номер: {data["Serial"]}\n' + \
        f'MAC: {data["MAC-address"]}' 

    return retval

def what_can_I_do():
    possibilities = ""
    possibilities += "Сказать id диалога /id\n" + \
        'Подписать на события от устройств /subscribeall'
    return possibilities

def save_chat_id(id):
    subscriptions_all.append(id)

@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Привет это бот для тестовых API Holy Tape\nВот что я могу делать:')
    bot.send_message(message.chat.id, what_can_I_do())

@bot.message_handler(commands=['id'])
def id_handler(message):
    bot.send_message(message.chat.id, 'Id этого диалога ' + str(message.chat.id))

@bot.message_handler(commands=['subscribeall','subscribebutton','subscribetemperature','subscribeco'])
def subscription_handler(message):
    save_chat_id(message.chat.id)
    bot.send_message(message.chat.id, 'Вы подписались на сообщения о всех событиях бота')


app = Flask(__name__)


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://htape-bot.herokuapp.com/' + TOKEN)
    return "!", 200


@app.route("/we/button", methods=['GET', 'POST'])
def button_event_handler():
    if request.method == 'POST':
        _content = request.json
        msg = make_button_message(_content)
        if msg is None:
            return {"utc_time": int(time.time())} 
        for id in subscriptions_all:
            bot.send_message(id, msg)
        return {"utc_time": int(time.time())}

@app.route("/api/v2/sensor/measures", methods=['GET', 'POST'])
def t_logger_event_handler():
    if request.method == 'POST':
        _content = request.json
        msg = None
        if _content['action'] == 'put_measures':
            msg = make_measures_message(_content)
        if msg is not None:
            for id in subscriptions_all:
                bot.send_message(id, msg)

    return {
        "utc_time": int(time.time()),
        "put_m_period_s": 60
        }

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

