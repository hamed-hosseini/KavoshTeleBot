import os
import telebot
from telebot import types
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from babel.numbers import format_decimal
token = "833040281:AAGZVzJCBFbMjnv1QnLYJYtnBSUlzsWjJS0"
prod_kw = {
    'name': 'نام', 'size': 'سایز', 'grade': 'درجه',
    'box_area': 'مساحت هر کارتن(مترمربع)' ,
    'count_in_box': 'تعداد برگ در هر بسته',
    'count_box': 'تعداد کارتن', 'price': 'قیمت هر متر مربع(تومان)',
    'date': 'تاریخ ثبت سفارش'
        }

bot = telebot.TeleBot(token)
knownUsers = []
product = {}


@bot.message_handler(commands=['start'])
def command_start(message):
    print(message)
    bot.reply_to(message, 'سلام به کاوش سرام خوش آمدید')
    # print(message.from_user.username)
    if check_admin(message):
        if not os.path.exists('pictures'):
            os.mkdir('pictures')
        main_menu_admin(message)
    elif check_co_worker(message):
        main_menu_client(message)
    else:
        message = bot.reply_to(message,
                               'هویت شما مورد تایید نمی باشد.'
                               ' با واحد پشتیبانی کاوش سرام تماس حاصل فرمایید و سپس تلاش کنید'
                               '\n'
                               'شماره تماس: 09123456592')
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
        restart = types.KeyboardButton('تلاش مجدد')
        markup.row(restart)
        message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
        bot.register_next_step_handler(message, command_start)


def main_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_existence = types.KeyboardButton('موجودی')
    item_sales_basket = types.KeyboardButton('سبد خرید')
    co_worker = types.KeyboardButton('همکاران')
    markup.row(item_existence, item_sales_basket, co_worker)
    message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, main_menu_admin_action)


def main_menu_client(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_existence = types.KeyboardButton('استعلام موجودی')
    item_sales_basket = types.KeyboardButton('سبد خرید')
    item_address = types.KeyboardButton('آدرس')
    markup.row(item_existence, item_sales_basket, item_address)
    message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, main_menu_client_action)


def main_menu_admin_action(message):
    if message.text == 'همکاران':
        co_worker_menu_admin(message)
    elif message.text == 'موجودی':
        existence_item_menu_admin(message)
    else:
        bot.reply_to(message, 'گزینه دیگری انتخاب کنید')
        main_menu_admin(message)


def main_menu_client_action(message):
    if message.text == 'استعلام موجودی':
        existence_item_search_client(message)
    elif message.text == 'آدرس':
        address_menu_client(message)
    elif message.text == 'سبد خرید':
        sale_basket_menu_client(message)
    else:
        bot.reply_to(message, 'گزینه دیگری انتخاب کنید')

def existence_item_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_existence = types.KeyboardButton('استعلام موجودی')
    item_sales_basket = types.KeyboardButton('افزودن کالای جدید')
    item_sales_exit_basket = types.KeyboardButton('وارد کردن کالای فروش رفته')
    item_main_menu = types.KeyboardButton('منو اصلی')
    markup.row(item_existence, item_sales_basket, item_main_menu)
    markup.row(item_sales_exit_basket)
    message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, existence_item_menu_admin_action)


def existence_item_menu_admin_action(message):
    if message.text == 'افزودن کالای جدید':
        add_name_admin(message)
    elif message.text == 'استعلام موجودی':
        df = db_to_df('select * from products').reset_index(drop=True)
        print(df)
        df.to_csv('Existance.csv')
        show_df_admin(message, df)
        with open('Existance.csv', 'r') as f:
            bot.send_document(message.chat.id, f)
        writeExcel(df, 'Existance','Existance')
        with open('Existance.xlsx', 'r') as f:
            bot.send_document(message.chat.id, f)
            existence_item_menu_admin(message)
    elif message.text == 'وارد کردن کالای فروش رفته':
        message = bot.reply_to(message, 'نام کالا را وارد کنید')
        bot.register_next_step_handler(message, check_detail)
    elif message.text == 'منو اصلی':
        main_menu_admin(message)
    else:
        existence_item_menu_admin(message)


def check_detail(message):
    df = db_to_df('select * from products').reset_index(drop=True)
    df_prod = df[df.name == message.text]
    if df.empty:
        bot.reply_to(message, 'این کالا موجود نمی باشد')
        existence_item_menu_admin(message)
    else:
        show_df_admin(message, df_prod)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
        item = []
        for i in range(len(df_prod)):
            item += [types.KeyboardButton(str(i + 1))]
            markup.row(item[i])
        message = bot.reply_to(message, 'ردیف مورد نظر را انتخاب کنید', reply_markup=markup)
        bot.register_next_step_handler(message, edit_prod, df_prod)


def edit_prod(message, df_prod):
    prod_id = df_prod.at[int(message.text) - 1, 'name'] + '-' +\
         df_prod.at[int(message.text) - 1, 'size'] + '-' + \
         df_prod.at[int(message.text) - 1, 'grade']
    print(prod_id)
    message = bot.reply_to(message, 'تعداد کارتن را وارد کنید')
    bot.register_next_step_handler(message, edit_carton_size, prod_id)


def edit_carton_size(message, id):
    df = db_to_df('select * from products').reset_index(drop=True)
    print(df)
    new_df = df[df.ID == id]
    print('new_df:', new_df)
    existing_count = new_df.at[0, 'count_box']
    df.set_value(df.ID == id, 'count_box', existing_count - int(message.text))
    df_to_db(df, 'kavoshbot', 'products')
    show_df_admin(message, df)
    existence_item_menu_admin(message)


@bot.message_handler(func=lambda message: True if message.text == 'استعلام موجودی' else False)
def existence_item_search_client(message):
    message = bot.reply_to(message, 'نام و یا سایز کالای مورد نظر را وارد نمایید')
    bot.register_next_step_handler(message, existence_item_search_client_action)


@bot.message_handler(func=lambda message: True if message.text == 'آدرس' else False)
def address_menu_client(message):
    bot.send_message(message.chat.id, 'بلوار آزادگان - خیابان سهیل - کوچه حسینی - بازرگانی کاوش سرام')
    bot.send_location(message.chat.id, 35.610928, 51.351182)


@bot.message_handler(func=lambda message: True if message.text == 'سبد خرید' else False)
def sale_basket_menu_client(message):
    query = 'select sale_basket.* , products.name, products.size, products.grade,' \
            ' products.box_area, products.count_in_box, products.price, products.file_id ' \
            'from sale_basket ' \
            'left join products on sale_basket.prod_ID = products.ID where user_ID="@{0}"'.format(
        message.from_user.username)
    print(query)
    try:
        df = db_to_df(query).reset_index(drop=True)
    except Exception:
        bot.send_message(message.chat.id, 'سبد خرید شما خالی است')
    else:
        show_sale_basket_client(message, df)


def existence_item_search_client_action(message):
    prod_client = data_cleaning(message.text)
    if check_is_size(prod_client):
        df_prod = db_to_df('select * from products where size="{0}"'.format(prod_client)).reset_index(drop=True)
    else:
        df_prod = db_to_df('select * from products where name="{0}"'.format(prod_client)).reset_index(drop=True)
    if df_prod.empty:
        bot.reply_to(message, 'کالایی با این نام یا سایز موجود نمی باشد')
    else:
        show_df_client(message, df_prod)


def data_cleaning(my_str):
    cleaned_str = ''.join(my_str.split(' '))
    return cleaned_str

def check_is_size(my_str):
    return '*' in my_str

def add_name_admin(message):
    message = bot.reply_to(message, 'نام کالا را وارد کنید')
    bot.register_next_step_handler(message, add_name_admin_action)


def add_name_admin_action(message):
    product['name'] = message.text
    add_size_menu_admin(message)


def add_size_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_60_30 = types.KeyboardButton('60*30')
    item_80_80 = types.KeyboardButton('80*80')
    item_58_58 = types.KeyboardButton('58*58')
    item_50_50 = types.KeyboardButton('50*50')
    item_60_60 = types.KeyboardButton('60*60')
    markup.row(item_60_30, item_80_80, item_58_58, item_50_50, item_60_60 )
    message = bot.reply_to(message, 'سایز را وارد کنید', reply_markup=markup)
    bot.register_next_step_handler(message, add_size_menu_admin_action)


def add_size_menu_admin_action(message):
    product['size'] = message.text
    add_grade_menu_admin(message)


def add_grade_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_a = types.KeyboardButton('A')
    item_b = types.KeyboardButton('B')
    item_c = types.KeyboardButton('C')
    item_1 = types.KeyboardButton('1')
    item_2 = types.KeyboardButton('2')
    item_3 = types.KeyboardButton('3')
    markup.row(item_a, item_b, item_c, item_1, item_2, item_3)
    message = bot.reply_to(message, 'گرید یا درجه را وارد کنید', reply_markup=markup)
    bot.register_next_step_handler(message, add_grade_menu_admin_action)


def add_grade_menu_admin_action(message):
    product['grade'] = message.text
    add_box_area_admin_menu(message)


def add_box_area_admin_menu(message):
    message = bot.reply_to(message, 'مساحت هر کارتن را وارد کنید')
    bot.register_next_step_handler(message, add_box_area_menu_admin_action)


def add_box_area_menu_admin_action(message):
    product['box_area'] = float(message.text)
    add_in_box_count_admin_menu(message)


def add_in_box_count_admin_menu(message):
    message = bot.reply_to(message, 'تعداد برگ هر کارتن را وارد کنید')
    bot.register_next_step_handler(message, add_in_box_count_menu_admin_action)


def add_in_box_count_menu_admin_action(message):
    product['count_in_box'] = int(message.text)
    add_box_count_menu_admin(message)


def add_box_count_menu_admin(message):
    message = bot.reply_to(message, 'تعداد کارتن را وارد کنید')
    bot.register_next_step_handler(message, add_box_count_menu_admin_action)


def add_box_count_menu_admin_action(message):
    product['count_box'] = int(message.text)
    add_box_price_menu_admin(message)


def add_box_price_menu_admin(message):
    message = bot.reply_to(message, 'قیمت هر متر مربع(تومان) را وارد کنید')
    bot.register_next_step_handler(message, add_box_price_menu_admin_action)


def add_box_price_menu_admin_action(message):
    product['price'] = int(message.text)
    add_image_menu_admin(message)


def add_image_menu_admin(message):
    message = bot.reply_to(message, 'عکس محصول را بارگذاری کنید')
    bot.register_next_step_handler(message, add_image_menu_admin_action)


def add_image_menu_admin_action(message):
    print(message.photo[3].file_id)
    product['file_id'] = message.photo[3].file_id
    file = bot.get_file(message.photo[3].file_id)
    downloaded_file = bot.download_file(file.file_path)
    with open(os.path.join(os.path.join(os.getcwd(), 'pictures'), message.photo[3].file_id + '.jpg'), 'wb') as f:
        f.write(downloaded_file)
    product['ID'] = product['name'] + '-' + product['size'] + '-' + product['grade']
    try:
        df = db_to_df('select * from products').reset_index(drop=True)
    except:
        df = pd.DataFrame(data=product, index=[0])
        df_to_db(df, 'kavoshbot', 'products')
        bot.reply_to(message, 'کالا با موفقیت ثبت گردید')
    else:
        if product['name'] not in df.name.values:
            df = df.append(product, ignore_index=True)
            df_to_db(df, 'kavoshbot', 'products')
            bot.reply_to(message, 'کالا با موفقیت ثبت گردید')
        else:
            bot.reply_to(message, 'این کالا قبلا ذخیره شده است')
    existence_item_menu_admin(message)


def co_worker_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_present_co_worker = types.KeyboardButton('همکاران فعلی')
    item_add_co_worker = types.KeyboardButton('افزودن همکار')
    item_delete_co_worker = types.KeyboardButton('حذف همکار')
    item_main_menu = types.KeyboardButton('منو اصلی')
    markup.row(item_present_co_worker, item_add_co_worker, item_main_menu, item_delete_co_worker)
    message = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(message, co_worker_menu_admin_action)


def co_worker_menu_admin_action(message):
    if message.text == 'همکاران فعلی':
        df_id = db_to_df('select * from authentication').reset_index(drop=True)
        list_id = df_id['ID'].tolist()
        bot.reply_to(message, '\n'.join(list_id))
        co_worker_menu_admin(message)
    elif message.text == 'افزودن همکار':
        getting_co_worker_id_admin(message)
    elif message.text == 'حذف همکار':
        message = bot.reply_to(message, 'آی دی همکار را وارد کنید مثلا: HMDhosseini@')
        bot.register_next_step_handler(message, co_worker_del_admin)
    elif message.text == 'منو اصلی':
        main_menu_admin(message)
    else:
        co_worker_menu_admin(message)


def co_worker_del_admin(message):
    co_ID = message.text
    df = db_to_df('select * from authentication').reset_index(drop=True)
    if co_ID not in df.ID.tolist():
        bot.reply_to(message, 'چنین آی دی در بین همکاران موجود نمی باشد')
        co_worker_menu_admin(message)
    else:
        df = df[df.ID != co_ID]
        df_to_db(df, 'kavoshbot', 'authentication')
        co_worker_menu_admin(message)
def getting_co_worker_id_admin(message):
    query = 'select * from authentication'
    df = db_to_df(query).reset_index(drop=True)
    bot.reply_to(message,'آی دی همکار را وارد کنید: مثلا HMDhosseini@')
    bot.register_next_step_handler(message, inserting_co_worker_id_admin)

def inserting_co_worker_id_admin(message):
    ID = message.text
    df = db_to_df('select * from authentication').reset_index(drop=True)
    if ID not in df.ID.values:
        df = df.append({'ID':ID}, ignore_index=True)
        df_to_db(df, 'kavoshbot', 'authentication')
        bot.reply_to(message, 'آی دی با موفقیت ثبت گردید')
    else:
        bot.reply_to(message, 'این آی دی قبلا ذخیره شده است')
    new_co_worker_menu_admin(message)

def new_co_worker_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    item_main_menu = types.KeyboardButton('بازگشت به منو اصلی')
    item_new_co_worker = types.KeyboardButton('افزودن همکار جدید')
    markup.row(item_main_menu, item_new_co_worker)
    msg = bot.reply_to(message, 'لطفا گزینه مورد نظر را انتخاب کنید', reply_markup=markup)
    bot.register_next_step_handler(msg, new_co_worker_menu_admin_action)
def new_co_worker_menu_admin_action(message):
    if message.text == 'بازگشت به منو اصلی':
        main_menu_admin(message)
    elif message.text == 'افزودن همکار جدید':
        getting_co_worker_id_admin(message)
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
    # df.drop(['file_id'], axis=1).reset_index(drop=True)
    db_connection.close()
    return df
def execute_query(query):
    db_name = 'kavoshbot'
    sqlEngine = create_engine('mysql+pymysql://root:Hamed31013711414@127.0.0.1/{0}'.format(db_name)
                              , pool_recycle=3600)
    db_connection = sqlEngine.connect()
    db_connection.execute(text(query))
    # df.drop(['file_id'], axis=1).reset_index(drop=True)
    db_connection.close()

def writeExcel(df,name, sheet):
    file_path = os.path.join(os.getcwd(), name + '.xlsx')
    from openpyxl import load_workbook
    try:
        book = load_workbook(file_path)
        writer = pd.ExcelWriter(file_path, engine='openpyxl', encoding='utf-8')
        writer.book = book
        print('sheet', sheet)
    except:
        writer = pd.ExcelWriter(file_path)

    df.to_excel(writer, sheet_name=sheet)
    writer.save()
    writer.close()
def show_df_admin(message, df):
    file_id = df['file_id']
    ID = df['ID']
    df = df.drop(['ID', 'file_id'], axis=1).reset_index(drop=True)
    all_prod = ''
    text = ''
    col = df.columns.tolist()
    print(col)
    for i in range(len(df)):
        my_list = df.loc[i, :].tolist()
        new_list = [str(prod_kw[col[j]]) + ':' + str(my_list[j]) for j in range(len(col))]
        text = str(i+1) + ': ' + ' - '.join(new_list)
        photo = open(os.path.join(os.path.join(os.getcwd(),'pictures'), str(file_id[i]) + '.jpg'), 'rb')
        # keyboard = types.InlineKeyboardMarkup()
        # item_add_to_sale = types.InlineKeyboardButton(text="افزودن به سبد خرید", callback_data='add_to_sale_basket_client-' + str(ID[i]))
        # keyboard.add(item_add_to_sale)
        bot.send_photo(message.chat.id, photo=photo, caption=text)
        all_prod += text + '\n'
def show_df_client(message, df):
    file_id = df['file_id']
    print(file_id)
    ID = df['ID']
    df = df.drop(['ID', 'file_id'], axis=1).reset_index(drop=True)
    all_prod = ''
    text = ''
    col = df.columns.tolist()
    print(col)
    for i in range(len(df)):
        my_list = df.loc[i, :].tolist()
        new_list = [str(prod_kw[col[j]]) + ':' + str(my_list[j]) for j in range(len(col)) if col[j] != 'price']
        new_list += [prod_kw['price'] + ':' + format_decimal(df.loc[i, 'price'], locale='en_US')]
        text = str(i+1) + ': ' + ' - '.join(new_list)
        photo = open(os.path.join(os.path.join(os.getcwd(), 'pictures'), str(file_id[i]) + '.jpg'), 'rb')
        keyboard = types.InlineKeyboardMarkup()
        item_add_to_sale = types.InlineKeyboardButton(text="افزودن به سبد خرید",
                                                      callback_data='add_to_sale_basket_client-' +
                                                                    str(ID[i]))
        keyboard.add(item_add_to_sale)
        bot.send_photo(message.chat.id, photo=photo, caption=text, reply_markup=keyboard)
        # bot.send_message(message.chat.id, "Я – сообщение из обычного режима", reply_markup=keyboard)
        all_prod += text + '\n'

def show_sale_basket_client(message, df):
    if not df.empty:
        keyboard = types.InlineKeyboardMarkup()
        item_empty_sale_basket = types.InlineKeyboardButton(text="خالی کردن سبد خرید",
                                                            callback_data='empty_sale_basket_client-'
                                                                          + str(df.loc[0, 'user_ID']))
        keyboard.add(item_empty_sale_basket)
        bot.send_message(message.chat.id, str(len(df)) + ' سفارش در سبد خرید شما است', reply_markup=keyboard)
        time_stamp = df['time_stamp']
        count_req = df['count']
        file_id = df['file_id']
        user_ID = df.loc[0, 'user_ID']
        df = df.drop(['user_ID', 'prod_ID', 'count', 'file_id', 'time_stamp'], axis=1).reset_index(drop=True)
        col = list(df.columns)
        total_price = 0
        for i in range(len(df)):
            total_price += count_req[i] * df.loc[i, 'price']
            my_list = df.loc[i, :].tolist()
            new_list = [str(prod_kw[col[j]]) + ':' + str(my_list[j]) for j in range(len(col)) if col[j] != 'price']
            new_list += [prod_kw['price'] + ':' + format_decimal(df.loc[i, 'price'], locale='en_US')]
            text = 'سفارش شماره' \
                   '{0}'.format(i+1) + ': ' + \
                   '\n\n' + ' - '.join(new_list) + \
                   '\n\n' + 'تعداد کارتن:' \
                          '{0}'.format(count_req[i]) + \
                   '\t' + 'متراژ:' + "{0:.2f}".format(df.loc[i, 'box_area'] * count_req[i])+ \
                   '\n\n' + 'قیمت پایه:' + \
                          '{0}'.format(format_decimal(df.loc[i, 'price'], locale='en_US')) + ' تومان'\
                   '\n' + 'قیمت کل' + \
                          '{0}'.format(format_decimal(count_req[i] * df.loc[i, 'price'], locale='en_US')) + ' تومان'\
                   '\n'
            keyboard = types.InlineKeyboardMarkup()
            item_delete_from_sale_basket = types.InlineKeyboardButton(text="حذف",
                                                                      callback_data='delete_from_sale_basket_client-'
                                                                                    + str(time_stamp[i]) + '-' + user_ID)
            keyboard.add(item_delete_from_sale_basket)
            photo = open(os.path.join(os.path.join(os.getcwd(),'pictures'), str(file_id[i]) + '.jpg'), 'rb')
            bot.send_photo(message.chat.id, photo=photo, caption=text, reply_markup=keyboard)
        keyboard = types.InlineKeyboardMarkup()

        item_empty_sale_basket = types.InlineKeyboardButton(text="نهایی کردن سفارش",
                                                            callback_data='finalize_sale_basket_client-'
                                                                          + user_ID)
        keyboard.add(item_empty_sale_basket)
        text = 'جمع کل سبد خرید:' + '\n' + format_decimal(total_price, locale='en_US')+ ' تومان'
        bot.send_message(message.chat.id, text , reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'سبد خرید شما خالی است')


def cal_area(my_size):
    height = my_size.split('*')[0]
    width = my_size.split('*')[1]
    return int(height) * int(width) / 10000
@bot.callback_query_handler(func=lambda call: True if 'add_to_sale_basket_client-' in call.data else False)
def callback_add_to_sale_basket_client(call):
    if call.message:
        if 'add_to_sale_basket_client-' in call.data:
            message = bot.send_message(call.message.chat.id, 'تعداد کارتن را وارد کنید')
            bot.register_next_step_handler(message, add_box_count_to_sale_basket_client, call)


@bot.callback_query_handler(func=lambda call: True if 'empty_sale_basket_client-' in call.data else False)
def callback_remove_sale_basket_client(call):
    if call.message:
        user_ID = call.data.split('empty_sale_basket_client-')[1]
        query = 'DELETE FROM sale_basket WHERE user_ID = "{0}";'.format(user_ID)
        execute_query(query)
        bot.send_message(call.message.chat.id, 'سبد خرید شما خالی شد')


@bot.callback_query_handler(func=lambda call: True if 'delete_from_sale_basket_client-' in call.data else False)
def callback_remove_sale_basket_client(call):
    if call.message:
        print(call.data)
        time_stamp = int(call.data.split('-')[1])
        user_ID = call.data.split('-')[2]
        query = 'DELETE FROM sale_basket WHERE user_ID="{0}" and time_stamp ="{1}";'.format(user_ID, time_stamp )
        execute_query(query)
        bot.send_message(call.message.chat.id, 'محصول از سبد خرید شما حذف شد')


def add_box_count_to_sale_basket_client(message, call):
    date = message.date
    count = int(message.text)
    prod_ID = call.data.split('add_to_sale_basket_client-')[1]
    user_ID = '@' + call.from_user.username
    try:
        df_sale = db_to_df('select * from sale_basket').reset_index(drop=True)
    except:
        df_sale = pd.DataFrame(data={'user_ID': user_ID, 'prod_ID': prod_ID, 'count': count, 'time_stamp': date}, index=[0])
        df_sale['date'] = pd.to_datetime(df_sale['time_stamp'], unit='s')
        df_to_db(df_sale, 'kavoshbot', 'sale_basket')
    else:
        df_sale = df_sale.append({'user_ID': user_ID, 'prod_ID': prod_ID, 'count': count, 'time_stamp': date}, ignore_index=True)
        df_sale['date'] = pd.to_datetime(df_sale['time_stamp'], unit='s')
        df_to_db(df_sale, 'kavoshbot', 'sale_basket')
    bot.send_message(message.chat.id, 'محصول به سبد خرید شما اضافه شد.')

    bot.send_message(message.chat.id, 'برای نهایی کردن سفارش میتوانید به سبد خرید رفته و یا برای جستجوی مجدد به بخش استعلام موجودی بروید')

def check_admin(message):
    if message.from_user.username == 'mjhossaini':
        return True
    else:
        return False

def check_co_worker(message):
    df_authen = db_to_df('select * from authentication').reset_index(drop=True)
    if '@' + message.from_user.username in df_authen['ID'].tolist():
        return True
    else:
        return False
print(bot.get_me())
#
# bot.enable_save_next_step_handlers(delay=1)
# bot.load_next_step_handlers()

bot.polling()
