import numpy as np
token = "833040281:AAGZVzJCBFbMjnv1QnLYJYtnBSUlzsWjJS0"
import telebot
from telebot import types
import pandas as pd
from pandas.io import sql
from sqlalchemy import create_engine

bot = telebot.TeleBot(token)
knownUsers = []
@bot.message_handler(commands=['start'])
def command_start(message):
    msg = bot.reply_to(message, 'سلام به کاوش سرام خوش آمدید')
    main_menu(message)
    #TODO: Authentication Evaluation
# @bot.message_handler()
# def command_start(message):
#     main_menu(message)
#     #TODO: Authentication Evaluation

def main_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_existance = types.KeyboardButton('استعلام موجودی')
    item_sales_bascket = types.KeyboardButton('سبد خرید')
    co_worker = types.KeyboardButton('همکاران')
    markup.row(item_existance, item_sales_bascket, co_worker)
    message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, main_menu_eval)

def main_menu_eval(message):
    if message.text == 'همکاران':
        co_worker_menu(message)
    else:
        bot.reply_to(message, 'گزینه دیگری انتخاب کنید')
        main_menu(message)
def co_worker_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_present_co_worker = types.KeyboardButton('همکاران فعلی')
    item_add_co_worker = types.KeyboardButton('افزودن همکار')
    item_main_menu = types.KeyboardButton('منو اصلی')
    markup.row(item_present_co_worker, item_add_co_worker, item_main_menu)
    msg = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, co_worker_menu_action)
def co_worker_menu_action(message):
    if message.text == 'همکاران فعلی':
        df_id = db_to_df('select * from authentication')
        list_id = df_id['ID'].tolist()
        bot.reply_to(message, '\n'.join(list_id))
        co_worker_menu(message)
    elif message.text == 'افزودن همکار':
        getting_co_worker_id(message)
    elif message.text == 'منو اصلی':
        main_menu(message)
    else:
        co_worker_menu(message)
def getting_co_worker_id(message):
    query = 'select * from authentication'
    df = db_to_df(query)
    bot.reply_to(message,'آی دی همکار را وارد کنید: مثلا HMDhosseini@')
    bot.register_next_step_handler(message, inserting_co_worker_id)

def inserting_co_worker_id(message):
    ID = message.text
    df = db_to_df('select * from authentication')
    if ID not in df.ID.values:
        df = df.append({'ID':ID}, ignore_index=True)
        df_to_db(df, 'kavoshbot', 'authentication')
        bot.reply_to(message, 'آی دی با موفقیت ثبت گردید')
    else:
        bot.reply_to(message, 'این آی دی قبلا ذخیره شده است')
    new_co_worker_menu(message)

def new_co_worker_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_main_menu = types.KeyboardButton('بازگشت به منو اصلی')
    item_new_co_worker = types.KeyboardButton('افزودن همکار جدید')
    markup.row(item_main_menu, item_new_co_worker)
    msg = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(msg, new_co_worker_action)
def new_co_worker_action(message):
    if message.text == 'بازگشت به منو اصلی':
        main_menu(message)
    elif message.text == 'افزودن همکار جدید':
        getting_co_worker_id(message)
def df_to_db(df, db_name, tabel_name):
    sqlEngine = create_engine('mysql+pymysql://root:Hamed31013711414@127.0.0.1/{0}'.format(db_name)
                              , pool_recycle=3600)
    db_connection = sqlEngine.connect()
    try:
        frame = df.to_sql(tabel_name, db_connection, if_exists='replace')
        print(frame)
    except ValueError as vx:
        print(vx)
    except Exception as ex:
        print(ex)
    else:
        print('Table {0} updated.'.format(tabel_name))
    finally:
        db_connection.close()

def db_to_df(query):
    db_name = 'kavoshbot'
    sqlEngine = create_engine('mysql+pymysql://root:Hamed31013711414@127.0.0.1/{0}'.format(db_name)
                              , pool_recycle=3600)
    db_connection = sqlEngine.connect()

    df = pd.read_sql(query, db_connection, index_col='index')
    db_connection.close()
    return df

def check_admin(message):
    if message.from_user['username'] == 'HMDhosseini':
        return True
    else:
        return False
print(bot.get_me())
authentication_dict = {

            'ID':['@HMDhosseini', '@mjhossaini']
            }
tableName = "authentication"

authentication_df = pd.DataFrame(data=authentication_dict).reset_index(drop=True)
df_to_db(authentication_df, 'kavoshbot', 'authentication')
data_frame = db_to_df('select * from authentication').reset_index(drop=True)
print(data_frame)
bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.polling()
