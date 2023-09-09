import random
from const import WIN_DICT, RAND_DICT
import pickle


# возвращение результатов матча
def round_judge(pl_obj):
    bot_obj = RAND_DICT[random.randint(1, 3)]
    # bot_obj - генерированное значение; pl_obj - значение игрока
    if pl_obj == bot_obj:
        return "no one's", bot_obj  # ничья
    elif WIN_DICT[pl_obj] == bot_obj:
        return "wins", bot_obj  # победа
    return "defeats", bot_obj  # поражение


# dd
# прочтение данных пользователя (при отсутствии создаст экземпляр)
def pickle_read(user_id):
    with open("data.pickle", "rb") as file:
        buffer = pickle.load(file)
        if user_id in buffer.keys():  # возвращение прочтенных данных
            return buffer[user_id]
        else:  # создание экземпляра по необходимости
            buffer[user_id] = {"wins": 0, "defeats": 0}

            # rf - file to read, wf - file to write
            with open("data.pickle", "wb") as wf:
                pickle.dump(buffer, wf)

            #  [user_id] = {"wins": 0, "defeats": 0}


# запись значений раундов в бд
def pickle_write(user_id, value):
    with open("data.pickle", "rb") as file:
        buffer = pickle.load(file)
        buffer[user_id][value] += 1
        with open("data.pickle", "wb") as f:
            pickle.dump(buffer, f)
    #  [user_id] = {"wins": 0, "defeats": 0}



