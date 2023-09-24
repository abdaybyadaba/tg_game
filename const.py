

WIN_DICT = {"камень": "ножницы",
            "ножницы": "бумага",
            "бумага": "камень"
            }  # can beat object

RAND_DICT = {1: "камень",
             2: "ножницы",
             3: "бумага"
             }  # randint_num - its submission in system

FIRST_DIALOGUE = "you started this bot \n" \
                "Now you able to play 'rock paper scissors'\n" \
                "I think you know rules, so lets start;)"

GIF_LIST = [None, None]
GIF_PATHS = ["static/wingif", "static/null"]
SCORE_MSG = "Вы: {}, Бот: {}"
REPLY_ROUND_MSG = "Вы: {}, Бот: {}, Осталось ходов: {}"
STATISTIC_MSG = "wins: {}, defeats: {}"
PATTERN = {"wins": 0, "defeats": 0, "steps": 3}
UNICODE_MAPPING = {"камень": '\U0001F5FF', "ножницы": '\U00002702', "бумага": '\U0001F9FB'}
