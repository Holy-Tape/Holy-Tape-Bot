from flask import Flask
import telebot
import os

TOKEN = os.environ.get('TOKEN', None)

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

def what_can_I_do():
    return "Пока ничего q_q"

@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Привет это бот для тестовых API Holy Tape\nВот что я могу делать:')
    bot.send_message(message.chat.id, what_can_I_do())
bot.polling()

@app.route("/")
def hello_world():
    return "Hello, World!"