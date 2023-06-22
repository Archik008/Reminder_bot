import telebot
import threading
import json
import schedule
import time
from telebot import types

bot = telebot.TeleBot('5722038528:AAGUvT08KENG8Lvbbm3Y4dmzGGWqxIB-81w')

my_data = ''


def opening_file():
    global my_data
    with open('data.json', 'r', encoding='utf-8') as myfile:
        my_data = json.load(myfile)

kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(types.KeyboardButton('Завершить удаление'))

kb_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb_cancel.add(types.KeyboardButton('Отменить действие'))

kb_every_day = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb_every_day.add(types.KeyboardButton('Каждый день'))

def run_scheduler():
    while True:
        schedule.run_pending()

opening_file()

@bot.message_handler(commands=['start'])
def get_id(msg):
    if str(msg.chat.id) not in my_data.keys():
        with open('data.json', 'w', encoding='utf-8') as writefile:
            json.dump({
                msg.chat.id:
                {
                
                }
            }, writefile, ensure_ascii=False)
        opening_file()
    else:
        bot.send_message(msg.chat.id, 'Привет! Я бот напоминалка. Напиши о чем я могу тебе напомнить.')

def send_reminder(timee):
    for id in my_data.keys():
        napominanie = my_data[id]
        napominanies_to_remove = []
        for key in napominanie.keys():
            if timee in napominanie[key] and not napominanie[key][timee]:
                if napominanie[key]['Frequency'] == 'Каждый день':
                    napominanie[key][timee] = True
                    bot.send_message(id, f'Напоминание!!!\n{key}')
                elif int(napominanie[key]['Frequency']) >= 1:
                    napominanie[key][timee] = True
                    napominanie[key]['Frequency'] -= 1
                    bot.send_message(id, f'Напоминание!!!\n{key}')
                else:
                    napominanies_to_remove.append(key)
        for key_removed in napominanies_to_remove:
            if key_removed in napominanie.keys():
                del napominanie[key_removed]
        save_data(my_data)
        


def update_msgs():
    for id in my_data.keys():
        napominanies = my_data[id]
        for napominanie_data in napominanies.values():
            for timee, boolean in napominanie_data.items():
                if boolean == True:
                    napominanie_data[timee] = False
    save_data(my_data)


deleting_msgs = {}


@bot.message_handler(commands=['show_reminders'])
def show_reminders(msg):
    chat_id = str(msg.chat.id)
    reminders = my_data.get(chat_id, {})
    if not reminders:
        bot.send_message(chat_id, 'У вас нет запланированных напоминаний.')
    else:
        message = 'Ваши напоминания:\n\n'
        for i, reminder in enumerate(reminders, 1):
            message += f'{i} - {reminder}\n'
        message += '\nОтправьте номера напоминаний, которые хотите удалить, через запятую (например, 1,3).\n'
        bot.send_message(chat_id, message, reply_markup=telebot.types.ForceReply())


def check_is_a_variaty(msg):
    try:
        texttt = list(msg.text)
        for symb in texttt:
            if symb == ' ':
                texttt.remove(symb)
        finished_variaties = ''.join(texttt).split(',')
        return True
    except:
        return False


@bot.message_handler(func=lambda message: message.reply_to_message is not None and 'Отправьте номера напоминаний' in message.reply_to_message.text and check_is_a_variaty)
def delete_reminders(msg):
    chat_id = str(msg.chat.id)
    napominanies = {}
    replied = msg.reply_to_message.text.split('\n\n')[1].split('\n')
    for napominanie in replied:
        napominanies[napominanie[0]] = napominanie[4:]
    texttt = list(msg.text)
    for symb in texttt:
        if symb == ' ':
            texttt.remove(symb)
    finished_variaties = ''.join(texttt).split(',')
    for variaty in finished_variaties:
        for napom_variaty in napominanies.keys():
            if variaty == napom_variaty:
                del my_data[chat_id][napominanies[variaty]]
    save_data(my_data)
    bot.send_message(msg.chat.id, 'Ваши выбранные напоминания удалены')
    

@bot.message_handler()
def get_data(msg):
    my_data[str(msg.chat.id)][msg.text] = None
    save_data(my_data)
    ask_time = bot.send_message(msg.chat.id, 'В какое время вы бы хотели запланировать это?', reply_markup=kb_cancel)
    bot.register_next_step_handler(ask_time, remind_handler)

def remind_handler(msg):
    if len(msg.text.split(':')[0]) == 2 and len(msg.text.split(':')[1]) == 2 and msg.text[2] == ':':
        if int(msg.text.split(':')[0]) <= 23 and int(msg.text.split(':')[1]) <= 59:
            napominanie = my_data[str(msg.chat.id)]
            for key, value in napominanie.items():
                if value == None:
                    napominanie[key] = {msg.text: False}
                    napominanie[key]['Frequency'] = None
                    save_data(my_data)
            set_time()
            ask_freq = bot.send_message(msg.chat.id, 'Сколько раз мне об этом напоминать?Напишите число или же "Каждый день"', reply_markup=kb_every_day)
            bot.register_next_step_handler(ask_freq, get_frequency)
        else:
            bot.send_message(msg.chat.id, 'Такого времени не бывает, напишите мне его еще раз.')
    elif msg.text == 'Отменить действие':
        bot.send_message(msg.chat.id, 'Действие отменено', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(msg.chat.id, 'Напишите мне еще раз время в формате "Часы и минуты", например 09:00')

def get_frequency(msg):
    try:
        napominanies = my_data[str(msg.chat.id)]
        if msg.text == 'Каждый день':
            for key in napominanies.keys():
                if napominanies[key]['Frequency'] == None:
                    napominanies[key]['Frequency'] = msg.text
            save_data(my_data)
            keyyyyt = list(napominanies.keys())[-1]
            bot.send_message(msg.chat.id, f'Ваше напоминание запланировано на: {list(napominanies[keyyyyt].keys())[0]}', reply_markup=types.ReplyKeyboardRemove())
        else:
            get_attempts = int(msg.text)
            for keyyy in napominanies.keys():
                if napominanies[keyyy]['Frequency'] == None:
                    napominanies[keyyy]['Frequency'] = get_attempts
                    napominanies[keyyy]['Frequency'] = int(napominanies[keyyy]['Frequency'])
            save_data(my_data)
            keyyyy = list(napominanies.keys())[-1]
            bot.send_message(msg.chat.id, f'Ваше напоминание запланировано на: {list(napominanies[keyyyy].keys())[0]}', reply_markup=types.ReplyKeyboardRemove())
    except:
        bot.send_message(msg.chat.id, 'Введите нормальный ответ')


def save_data(mydata):
    with open('data.json', 'w', encoding='utf-8') as wfile:
        json.dump(mydata, wfile, ensure_ascii=False, indent=3)


def set_time():
    for id in my_data.keys():
        for value in my_data[id].values():
            if value != None and len(list(my_data[id].values())[0]) != 0:
                timeee = list(value.keys())[0]
                schedule.every().day.at(timeee).do(send_reminder, timeee)


set_time()

schedule.every().day.do(update_msgs)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    bot_thread.start()

    time_thread = threading.Thread(target=run_scheduler, daemon=True)
    time_thread.start()

    while True:
        time.sleep(1)