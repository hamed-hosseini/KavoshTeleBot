import numpy as np
# import telepot
token = "875871238:AAErva9If3i1rnhJT-ZGQBpsrJtg5uR6YqA"
# TelegramBot = telepot.Bot(token)
# print(TelegramBot.getMe())

# import os
# hostname = "core.telegram.org" #example
# response = os.system("ping " + hostname)

import telebot

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "چجوری میتونم کمکتون کنم")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

print(bot.get_me())
text = 'Hamed is writting a bot'
bot.polling()
