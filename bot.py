import sqlite3
import telebot
import config
import random
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InputFile

# Подключение к базе данных
conn = sqlite3.connect('Ques.db', check_same_thread=False)
cursor = conn.cursor()

i=0
user_data = {}

bot = telebot.TeleBot(config.TOKEN)

# Получение всех вопросов из базы данных
cursor.execute("SELECT * FROM questions")
all_questions = cursor.fetchall()

# Перемешивание вопросов
random.shuffle(all_questions)

# Создание списка для хранения использованных вопросов
used_questions = []

@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard_start = ReplyKeyboardMarkup(row_width=1)
    start_button = KeyboardButton('Старт')
    keyboard_start.add(start_button)
    msg = 'Привет! Я бот для тестирования по математике. Данный тест направлен на проверку математической грамотности. Вот тебе небольшая инструкция:\nПосле каждого вопроса тебе будет предоставлен выбор:\n"Да", тебе дается следующий вопрос\n"Нет" тебе зачитывается столько вопросов, сколько ты решил.\nЕсли ты случайно нажал кнопку "Нет", то можешь пройти тест заново командой /test, но занай у тебя всего лишь 5 попыток и будет зачитываться только лучишй результат.\nОБЯЗАТЕЛЬНО:\nЕсли у тебя получилось не целое число, то записывай с точкой (Например: 1.5)\n Удачи!'
    bot.send_message(message.chat.id, msg)
    msg1 ="Напиши /test"
    bot.send_message(message.chat.id, msg1)
    
    
@bot.message_handler(commands=['test'])
def start_message(message):
    global used_questions
    used_questions = []
    
    msg = 'Начнем!\nКак тебя зовут?'
    bot.send_message(message.chat.id, msg)
    # Устанавливаем состояние "waiting_for_name" для ожидания имени пользователя
    bot.register_next_step_handler(message, process_name)

def process_name(message):
    # Сохраняем имя пользователя в словаре user_data
    user_data['user_name'] = message.text
    msg = 'Отлично! Теперь введи свою фамилию.'
    bot.send_message(message.chat.id, msg)
    # Устанавливаем состояние "waiting_for_surname" для ожидания фамилии пользователя
    bot.register_next_step_handler(message, process_surname)

def process_surname(message):
    # Сохраняем фамилию пользователя в словаре user_data
    user_data['surname'] = message.text
    
    connect = sqlite3.connect('users.db')
    cursour_user = connect.cursor()
    nowUser = message.chat.id
    
    print("User id login now:")
    print(nowUser)
    
    cursour_user.execute(f"SELECT id FROM users WHERE id={nowUser}")
    data = cursour_user.fetchone()
    
    if data is None:
        print("Такого пользователя нет, записываю в бд")
        t = 1 
        cursour_user.execute(f"INSERT INTO users VALUES (?,?,?,?,?)", (nowUser, user_data['user_name'], user_data['surname'], i, t))
        connect.commit()
        msg = f'{user_data["user_name"]} {user_data["surname"]} готов начать тест?'
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='button1')],
            [InlineKeyboardButton("Нет", callback_data='button2')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
    
    else:
        cursour_user.execute(f"SELECT user_try FROM users WHERE id={nowUser}")
        t = cursour_user.fetchone()[0]
                
        if t <= 5:
            print("User trys:")
            print(t)
              
            cursour_user.execute(f"UPDATE users SET user_try = '{t}' WHERE id = '{nowUser}'")
            connect.commit()
            msg = f'{user_data["user_name"]} {user_data["surname"]} готов начать тест?'
            keyboard = [
                [InlineKeyboardButton("Да", callback_data='button1')],
                [InlineKeyboardButton("Нет", callback_data='button2')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(message.chat.id, msg, reply_markup=reply_markup)     
        else:     
                cursour_user.execute(f"SELECT userResault FROM users WHERE id={nowUser}")
                res = cursour_user.fetchone()[0]
                bot.send_message(message.chat.id, f'{user_data["user_name"]} {user_data["surname"]} вы уже использовали все ваши попытки! Ваш последний тест был пройден на {res} из 5')
                

        
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global used_questions
    global i

    connect = sqlite3.connect('users.db')
    cursour = connect.cursor()
    user_id = call.message.chat.id
    
    cursour.execute(f"SELECT user_try FROM users WHERE id={user_id}")
    t = cursour.fetchone()[0] 
    
    cursour.execute(f"SELECT userResault FROM users WHERE id={user_id}")
    userRes = cursour.fetchone()[0] 
    
    if call.data == 'button1':
        # Проверяем, есть ли еще доступные вопросы
        if len(used_questions) <= len(all_questions):
            # Поиск следующего неиспользованного вопроса
            question = None
            for q in all_questions:
                if q[0] not in used_questions:
                    question = q
                    break
            
            if question:
                question_id = question[0]
                question_text = question[1]
                correct_answer = question[2]
                img_id = question[3]
                used_questions.append(question_id)

                # Отправляем вопрос пользователю
                if  img_id == 1:
                    p2 = open('img/Capture2.PNG', 'rb')
                    bot.send_photo(call.message.chat.id, p2)
                    bot.send_message(call.message.chat.id, text=question_text)    
                elif  img_id == 2:
                    p = open('img/Capture.PNG', 'rb')
                    bot.send_photo(call.message.chat.id, p)
                    bot.send_message(call.message.chat.id, text=question_text)
                else:
                    bot.send_message(call.message.chat.id, text=question_text)
            else:
                bot.send_message(call.message.chat.id, f'{user_data["user_name"]} {user_data["surname"]} вопросы закончились. Ты решил {i} из 5. Пройти снова пропиши /start')             
                t+=1
                print("User trys:")
                print(t)
                
                print("User previous resault: ")
                print(userRes)
                print(i)
                
                if userRes > i:
                    cursour.execute(f"UPDATE users SET user_try = '{t}' WHERE id = '{user_id}'")
                    connect.commit() 
                    connect.close()
                    print("Результат не обновлен тк прошлый результат был больше чем текущий") 
                    i=0          
            
                else:
                    cursour.execute(f"UPDATE users SET userResault = '{i}', user_try = '{t}' WHERE id = '{user_id}'")
                    connect.commit() 
                    connect.close()
                    print("Записано, так как прошый рещультат был меньше")
                    i = 0
        else:
            bot.send_message(call.message.chat.id, f'{user_data["user_name"]} {user_data["surname"]} вопросы закончились. Ты решил {i} из 5. Пройти снова пропиши /start')  
                 
            t+=1
            print("User trys:")
            print(t)
             
            print("User previous resault: ")
            print(userRes)
            print(i)
            
            if userRes > i:
                cursour.execute(f"UPDATE users SET user_try = '{t}' WHERE id = '{user_id}'")
                connect.commit() 
                connect.close()
                print("Результат не обновлен тк прошлый результат был больше чем текущий") 
                i=0          
            
            else:
                cursour.execute(f"UPDATE users SET userResault = '{i}', user_try = '{t}' WHERE id = '{user_id}'")
                connect.commit() 
                connect.close()
                print("Записано, так как прошый рещультат был меньше")
                i = 0
    elif call.data == 'button2':
        bot.send_message(call.message.chat.id, f'{user_data["user_name"]} {user_data["surname"]} тестирование завершено. Ты решил {i} из 5. Пройти снова пропиши /start' )            
        t+=1
        print("User trys:")
        print(t)
        
        
        print("User previous resault: ")
        print(userRes)
        print(i)
         
        if userRes > i:
            cursour.execute(f"UPDATE users SET user_try = '{t}' WHERE id = '{user_id}'")
            connect.commit() 
            connect.close()
            print("Результат не обновлен тк прошлый результат был больше чем текущий") 
            i=0          
            
        else:
            cursour.execute(f"UPDATE users SET userResault = '{i}', user_try = '{t}' WHERE id = '{user_id}'")
            connect.commit() 
            connect.close()
            print("Записано, так как прошый рещультат был меньше")
            i = 0

@bot.message_handler(func=lambda message: True)
def test_message(message):
    global i
    global t
    
    connect = sqlite3.connect('users.db')
    cursour = connect.cursor()
    user_id = message.chat.id 
    
    cursour.execute(f"SELECT userResault FROM users WHERE id={user_id}")
    userRes = cursour.fetchone()[0] 
    
    cursour.execute(f"SELECT user_try FROM users WHERE id={user_id}")
    t = cursour.fetchone()[0]
    
    # Проверяем, есть ли еще доступные вопросы
    if len(used_questions) <= len(all_questions):
        # Получаем последний использованный вопрос
        question_id = used_questions[-1]
        question = next((q for q in all_questions if q[0] == question_id), None)
        
        if question:
            correct_answer = question[2]

            # Проверяем ответ пользователя на последний вопрос
            if message.text.strip().lower() == correct_answer.strip().lower():               
                i+=1
                bot.reply_to(message, 'Правильно!')
                msg ='Идем дальше?'
                keyboard = [
                [InlineKeyboardButton("Да", callback_data='button1')],
                [InlineKeyboardButton("Нет", callback_data='button2')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
            else:
                bot.reply_to(message, 'Неправильно!')
                msg ='Идем дальше?'
                keyboard = [
                [InlineKeyboardButton("Да", callback_data='button1')],
                [InlineKeyboardButton("Нет", callback_data='button2')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
    else:
        bot.reply_to(message, f'{user_data["user_name"]} {user_data["surname"]} вопросы закончились. Ты решил {i} из 5. Пройти снова пропиши /start')              
        t+=1
        print("User trys:")
        print(t)   
        
        print("User previous resault: ")
        print(userRes)
         
        if userRes > i:
            cursour.execute(f"UPDATE users SET user_try = '{t}' WHERE id = '{user_id}'")
            connect.commit() 
            connect.close()
            print("Результат не обновлен тк прошлый результат был больше чем текущий")  
            i=0         
            
        else:
            cursour.execute(f"UPDATE users SET userResault = '{i}', user_try = '{t}' WHERE id = '{user_id}'")
            connect.commit() 
            connect.close()
            print("Записано, так как прошый рещультат был меньше")
            i=0

        
bot.polling()