import asyncio
import os
import logging
from copy import deepcopy
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
bot.chat_id = {}
bot.message_id = {}

# значения раунда

bot.main_score = {}

# сообщения раунда (под удаление)
bot.delete_list = {}


async def delete_messages(user_id):
    if bot.delete_list[user_id]:  # удаление сообщений раунда
        print(bot.delete_list)
        for mes in bot.delete_list[user_id]:
            await bot.delete_message(chat_id=mes.chat.id, message_id=mes.message_id)
        bot.delete_list[user_id] = []


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

    bot.main_score[user_id] = deepcopy(PATTERN)
    await delete_messages(user_id)

    # возвращение сообщения\действия
    await bot.edit_message_text(chat_id=bot.chat_id[user_id], message_id=bot.message_id[user_id], text=FIRST_DIALOGUE)
    await bot.edit_message_reply_markup(chat_id=bot.chat_id[user_id],
                                            message_id=bot.message_id[user_id], reply_markup=await menu_kb_builder())


async def check_round_over(call: types.CallbackQuery):
    user_id = call.from_user.id
    if not bot.main_score[user_id]["steps"]:  # возвращение результатов и закрытие сообщения
        if bot.main_score[user_id]["wins"] != bot.main_score[user_id]["defeats"]:
            # запись результата матча в бд
            if bot.main_score[user_id]["wins"] > bot.main_score[user_id]["defeats"]:
                pickle_write(user_id, "wins")
            else:
                pickle_write(user_id, "defeats")
            await back_to_menu(user_id)
        else:
            bot.main_score[user_id]["steps"] += 1


@dp.message(Command("start"))  # создание стартового и главного сообщения
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    # проверка (если в буферных переменных есть данные сообщения то при запросе start ничего не произойдет)
    if user_id not in bot.chat_id:
        bot.main_score[user_id] = deepcopy(PATTERN)
        bot.delete_list[user_id] = []
        logging.info("here you are")
        pickle_read(user_id)

        # создание сообщения и добавления его данных в переменные для последующего изменения
        sent_message = await msg.answer(FIRST_DIALOGUE, reply_markup=await menu_kb_builder())
        bot.chat_id[user_id], bot.message_id[user_id] = sent_message.chat.id, sent_message.message_id


@dp.callback_query(F.data == "game")
async def from_main_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    await bot.edit_message_text(chat_id=bot.chat_id[user_id],
                                message_id=bot.message_id[user_id],
                                text=REPLY_ROUND_MSG.format(0, 0, 0))

    await bot.edit_message_reply_markup(chat_id=bot.chat_id[user_id],
                                        message_id=bot.message_id[user_id],
                                        reply_markup=await game_kb_builder())


@dp.callback_query(F.data == "statistic")
async def statistic_mes(callback: types.CallbackQuery):
    logging.info("statistic")
    user_id = callback.from_user.id
    print(bot.chat_id, bot.message_id)
    # выводимые тексты
    ans_p = pickle_read(callback.from_user.id)
    ans_text = STATISTIC_MSG.format(ans_p["wins"], ans_p["defeats"])

    # создание клавиатуры
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="back to menu", callback_data="back to menu"))

    # создание сообщения и добавления его данных в переменные для последующего изменения
    await bot.edit_message_text(chat_id=bot.chat_id[user_id],
                                message_id=bot.message_id[user_id],
                                text=ans_text)
    logging.info("statistic2")
    await bot.edit_message_reply_markup(chat_id=bot.chat_id[user_id],
                                            message_id=bot.message_id[user_id],
                                        reply_markup=builder.as_markup())


@dp.callback_query(F.data.in_({"камень", "ножницы", "бумага"}))
async def from_main_menu(callback: types.CallbackQuery):

    user_id = callback.from_user.id
    result = round_judge(callback.data)
    bot.main_score[user_id]["steps"] -= 1  # убавление \ добавление ходов (при ничье)

    if result[0] == "no one's":
        bot.main_score[user_id]["steps"] = bot.main_score[user_id]["steps"] + 1
    else:  # запись результатов матча внутри раунда в словарь main_score
        bot.main_score[user_id][result[0]] += 1

    # выводные сообщения
    ans = SCORE_MSG.format(callback.data, result[1], result[0])
    ans_mes_text = REPLY_ROUND_MSG.format(bot.main_score[user_id]["wins"],
                                          bot.main_score[user_id]["defeats"],
                                          bot.main_score[user_id]["steps"])

    await bot.edit_message_text(chat_id=bot.chat_id[user_id],
                                message_id=bot.message_id[user_id],
                                text=ans_mes_text)
    await bot.edit_message_reply_markup(chat_id=bot.chat_id[user_id],
                                            message_id=bot.message_id[user_id],
                                        reply_markup=await game_kb_builder())

    n_message = await callback.message.answer(text=ans)
    # if callback.from_user.id not in delete_list.keys:
    #     delete_list[callback.from_user.id] = []
    print(n_message)
    bot.delete_list[user_id].append(n_message)
    await check_round_over(callback)
    print(bot.main_score)


@dp.callback_query(F.data == "back to menu")
async def back_mes(call: types.CallbackQuery):
    await back_to_menu(call.from_user.id)

dp.message.register(cmd_start, Command("start"))


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.info("Bot started")
    asyncio.run(main())
