from flask import Flask
from flask import request
from werkzeug.utils import secure_filename

import time 
import telebot
import os
import psycopg2

DB_URL = os.environ.get('DATABASE_URL', None)
TOKEN = os.environ.get('TOKEN', None)
HKD_SUB = [os.environ.get('HKD_SUB', None)]



UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

last_photo = "No photo"

# conn = psycopg2.connect(dbname='database', user='db_user', 
#                         password='mypassword', host=DB_URL)
# cursor = conn.cursor()

bot = telebot.TeleBot(TOKEN)

subscriptions_all = set(HKD_SUB)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    subscriptions_all.add(id)

@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Привет это бот для тестовых API Holy Tape\nВот что я могу делать:')
    bot.send_message(message.chat.id, what_can_I_do())

@bot.message_handler(commands=['id'])
def id_handler(message):
    bot.send_message(message.chat.id, 'Id этого диалога ' + str(message.chat.id))

@bot.message_handler(commands=['subscribeall','subscribebutton','subscribetemperature','subscribeco', 'subscribephoto'])
def subscription_handler(message):
    save_chat_id(message.chat.id)
    bot.send_message(message.chat.id, 'Вы подписались на сообщения о всех событиях бота')


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        "put_m_period_s": 300
        }

@app.route("/put-photo", methods=['GET', 'POST'])
def photo_handler():
    if request.method == 'POST':
        if 'image' not in request.files:
            print('No file part')
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            print('No selected file')
            return 'No selected file', 400
        if file and allowed_file(file.filename):
            last_photo = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], last_photo)
            file.save(filepath)
            img = open(filepath, 'rb')
            for id in subscriptions_all:
                if id is not '':
                    img = open(filepath, 'rb')
                    bot.send_photo(id, img)
            # Here we must send photo
            return 'Success\n', 200
    if request.method == 'GET':
        return last_photo, 200


@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url='https://htape-bot.herokuapp.com/' + TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))