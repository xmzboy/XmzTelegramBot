import re
import requests
from typing import Dict
from random import choice, randint
import telebot
from telebot import types
from markup import reply_markup_start, reply_markup_end, reply_markup_new_game, reply_markup_help
import constants
from hangman_game import HangmanGame

bot = telebot.TeleBot(constants.TOKEN)
games: Dict[int, HangmanGame] = {}

film_list = ["Однажды в Голливуде", "Семь психопатов", "Бойцовский клуб",
             "Три биллборда на границе Эббинга и Миссури", "Дикие истории",
             "Залечь на дно в Брюгге", "Голгофа", "Большая афера",
             "Большой куш", "Однажды в Ирландии", "Гнев человеческий",
             "Карты, деньги, два ствола", "Джентельмены", "Большой Лебовски"]

book_list = ["Семь навыков высокоэффективных людей", "Богатый папа, бедный папа",
             "Властелин Колец", "Хоббит", "Зов Ктулху", "1984", "Восьмой навык"]

habr_list = ['https://habr.com/ru/post/245065/', 'https://habr.com/ru/post/302914/']

seq = [randint(240000, 600000) for _ in range(30)]
for i in range(len(seq)):
    try:
        response = requests.head('https://habr.com/ru/post/' + str(seq[i]))
        if response.status_code == 200:
            habr_list.append('https://habr.com/ru/post/' + str(seq[i]))
    except Exception as ex:
        print(ex)


@bot.message_handler(commands=['start'])
def start_command(message: telebot.types.Message) -> None:
    bot.send_photo(message.from_user.id, 'https://avatars.mds.yandex.net/get-zen_doc/1875939/'
                                         'pub_612e3698fc890f70eef3b674_612e36c5e9fa270869a2cb37/scale_1200')
    keyboard1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/start")
    item2 = types.KeyboardButton("/help")
    keyboard1.add(item1)
    keyboard1.add(item2)
    bot.send_message(message.from_user.id, text='У нас много интересного для тебя!', reply_markup=keyboard1)
    keyboard = types.InlineKeyboardMarkup()
    key_film = types.InlineKeyboardButton(text='Какой фильм посмотреть?', callback_data='film')
    keyboard.add(key_film)
    key_book = types.InlineKeyboardButton(text='Какую книгу прочитать?', callback_data='book')
    keyboard.add(key_book)
    key_hangman = types.InlineKeyboardButton(text='Сыграть в виселицу', callback_data='hangman')
    keyboard.add(key_hangman)
    key_habr = types.InlineKeyboardButton(text='Статья с Хабра', callback_data='habr')
    keyboard.add(key_habr)
    bot.send_message(message.from_user.id, text='Выбери:', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: telebot.types.CallbackQuery) -> None:
    if call.data == "film":
        film_choice = choice(film_list)
        bot.send_message(call.from_user.id, "Мне кажется тебе понравится этот фильм👇🏻")
        bot.send_message(call.from_user.id, film_choice)
    elif call.data == "book":
        book_choice = choice(book_list)
        bot.send_message(call.from_user.id, "Познакомься с этой книгой👇🏻")
        bot.send_message(call.from_user.id, book_choice)
    elif call.data == "hangman":
        show_choice(call.from_user.id, constants.START_TEXT, reply_markup_start)
    elif call.data == "habr":
        habr_choice = choice(habr_list)
        bot.send_message(call.from_user.id, "Крайне полезная статья👇🏻")
        text = f'[Статья]({habr_choice})'
        bot.send_message(call.from_user.id, text, parse_mode='MarkdownV2')
    elif call.data == "yes":
        go_command(call.message.chat.id)
    elif call.data == "no":
        bot.send_message(call.message.chat.id, constants.GOODBYE_TEXT)
        start_command(call.message)
    elif call.data == "go":
        go_command(call.message.chat.id)
    elif call.data == "rules":
        rules_command(call.message.chat.id)
    elif call.data == "help":
        help_command(call.message.chat.id)


def help_command(chat_id: int) -> None:
    show_choice(chat_id, constants.HELP_TEXT, types.InlineKeyboardMarkup())


def rules_command(chat_id: int) -> None:
    show_choice(chat_id, constants.RULES_TEXT, reply_markup_new_game)


def go_command(chat_id: int) -> None:
    if chat_id not in games.keys():
        games[chat_id] = HangmanGame()
    games[chat_id].new_level()

    bot.send_message(chat_id, games[chat_id].current_hidden_word)
    bot.send_message(chat_id, constants.SEND_LTR_TEXT)


@bot.message_handler(content_types=['text'])
def reception_text(message: telebot.types.Message) -> None:
    if message.chat.id not in games.keys():
        show_choice(message.chat.id, 'Чтобы узнать функции бота нажмите /help', reply_markup_help)
        # show_choice(message.chat.id, constants.WARNING_TEXT, reply_markup_new_game)
    elif is_incorrect_input(message.text.lower()):
        bot.send_message(message.chat.id, constants.SEND_LTR_TEXT)
    else:
        send_game_message(message)


def send_game_message(message: telebot.types.Message) -> None:
    chat_id: int = message.chat.id
    if games[chat_id].is_true_letter(message.text.lower()):
        bot.send_message(chat_id, games[chat_id].current_hidden_word)
        if games[chat_id].is_guessed_word():
            show_choice(chat_id, constants.WIN_TEXT, reply_markup_end)
            del games[chat_id]
    else:
        bot.send_photo(chat_id, photo=games[chat_id].current_stage)
        bot.send_message(chat_id, games[chat_id].current_hidden_word)
        if games[chat_id].is_game_over():
            show_choice(chat_id, constants.GAME_OVER_TEXT % games[chat_id].current_word, reply_markup_end)
            del games[chat_id]


def show_choice(chat_id: int, text: str, reply_markup: telebot.types.InlineKeyboardMarkup) -> None:
    bot.send_message(chat_id, text=text, reply_markup=reply_markup)


def is_incorrect_input(input_text: str) -> bool:
    return len(input_text) > 1 or re.match('[а-я]', input_text) is None
