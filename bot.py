import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from const import *
from aiogram.utils.keyboard import InlineKeyboardBuilder
from backend import round_judge, pickle_read, pickle_write
from aiogram import F
from aiogram.handlers import CallbackQueryHandler
from aiogram.filters.callback_data import CallbackQueryFilter, CallbackData
load_dotenv()

bot = Bot(token=os.getenv("API_TOKEN"))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
# служат для изменения основного сообщения
chat_id = None
message_id = None

# значения раунда
pattern = {"wins": 0, "defeats": 0, "steps": 3}
main_score = {}

# сообщения раунда (под удаление)
delete_list = {}


async def delete_messages(user_id):
    global delete_list
    if delete_list[user_id]:  # удаление сообщений раунда
        print(delete_list)
        for mes in delete_list[user_id]:
            await bot.delete_message(chat_id=mes.chat.id, message_id=mes.message_id)
        delete_list = []


async def menu_kb_builder():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="game", callback_data="game"),
                types.InlineKeyboardButton(text="statistic", callback_data="statistic"))
    return builder.as_markup()


async def game_kb_builder():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="камень", callback_data="камень"),
                types.InlineKeyboardButton(text="ножницы", callback_data="ножницы"),
                types.InlineKeyboardButton(text="бумага", callback_data="бумага"),
                )
    builder.row(types.InlineKeyboardButton(text="back to menu", callback_data="back to menu"))
    return builder.as_markup()


async def back_to_menu(user_id):
    global chat_id, message_id, main_score, pattern

    main_score[user_id] = pattern
    await delete_messages(user_id)

    # возвращение сообщения\действия
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=FIRST_DIALOGUE)
    await bot.edit_message_reply_markup(chat_id=chat_id,
                                            message_id=message_id, reply_markup=await menu_kb_builder())


async def check_round_over(call: types.CallbackQuery):
    global main_score
    if not main_score[call.from_user.id]["steps"]:  # возвращение результатов и закрытие сообщения
        if main_score[call.from_user.id]["wins"] != main_score[call.from_user.id]["defeats"]:
            # запись результата матча в бд
            if main_score[call.from_user.id]["wins"] > main_score[call.from_user.id]["defeats"]:
                pickle_write(call.from_user.id, "wins")
            else:
                pickle_write(call.from_user.id, "defeats")
            await back_to_menu(call.from_user.id)
        else:
            main_score[call.from_user.id]["steps"] += 1


@dp.message(Command("start"))  # создание стартового и главного сообщения
async def cmd_start(mes: types.Message):
    global chat_id, message_id, main_score, delete_list, pattern

    # проверка (если в буферных переменных есть данные сообщения то при запросе start ничего не произойдет)
    if not any([chat_id, message_id]):
        main_score[mes.from_user.id] = pattern
        delete_list[mes.from_user.id] = []
        logging.info("here you are")
        pickle_read(mes.from_user.id)

        # создание сообщения и добавления его данных в переменные для последующего изменения
        sent_message = await mes.answer(FIRST_DIALOGUE, reply_markup=await menu_kb_builder())
        chat_id, message_id, mesa = sent_message.chat.id, sent_message.message_id, sent_message


@dp.callback_query(F.data == "game")
async def from_main_menu(call: types.CallbackQuery):
    global chat_id, message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=REPLY_ROUND_MSG.format(0, 0, 0))
    await bot.edit_message_reply_markup(chat_id=chat_id,
                                            message_id=message_id, reply_markup=await game_kb_builder())


@dp.callback_query(F.data == "statistic")
async def statistic_mes(callback: types.CallbackQuery):
    logging.info("statistic")
    global chat_id, message_id
    print(chat_id, message_id)
    # выводимые тексты
    ans_p = pickle_read(callback.from_user.id)
    ans_text = STATISTIC_MSG.format(ans_p["wins"], ans_p["defeats"])

    # создание клавиатуры
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="back to menu", callback_data="back to menu"))

    # создание сообщения и добавления его данных в переменные для последующего изменения
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=ans_text)
    logging.info("statistic2")
    await bot.edit_message_reply_markup(chat_id=chat_id,
                                            message_id=message_id, reply_markup=builder.as_markup())


@dp.callback_query(F.data.in_({"камень", "ножницы", "бумага"}))
async def from_main_menu(callback: types.CallbackQuery):
    global chat_id, message_id, delete_list, main_score

    result = round_judge(callback.data)
    main_score[callback.from_user.id]["steps"] -= 1  # убавление \ добавление ходов (при ничье)

    if result[0] == "no one's":
        main_score[callback.from_user.id]["steps"] = main_score[callback.from_user.id]["steps"] + 1
    else:  # запись результатов матча внутри раунда в словарь main_score
        main_score[callback.from_user.id][result[0]] += 1

    # выводные сообщения
    ans = SCORE_MSG.format(callback.data, result[1], result[0])
    ans_mes_text = REPLY_ROUND_MSG.format(main_score[callback.from_user.id]["wins"],
                                          main_score[callback.from_user.id]["defeats"],
                                          main_score[callback.from_user.id]["steps"])

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=ans_mes_text)
    await bot.edit_message_reply_markup(chat_id=chat_id,
                                            message_id=message_id, reply_markup=await game_kb_builder())

    n_message = await callback.message.answer(text=ans)
    # if callback.from_user.id not in delete_list.keys:
    #     delete_list[callback.from_user.id] = []
    print(n_message)
    delete_list[callback.from_user.id].append(n_message)
    await check_round_over(callback)


@dp.callback_query(F.data == "back to menu")
async def back_mes(call: types.CallbackQuery):
    await back_to_menu(call.from_user.id)

dp.message.register(cmd_start, Command("start"))


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.info("Bot started")
    asyncio.run(main())
