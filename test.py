
# import pickle
#
#
# data = {"user": {"wins": 0, "defeats": 0}}
#
# with open("data.pickle", "wb") as file:
#     pickle.dump(data, file)
#
#
# with open("data.pickle", "rb") as file:
#     print(pickle.load(file))


class Defeat:
    pass


class Win:
    pass


class GameResultState:
    DEFEAT = Defeat()
    WIN = Win()


player = 3
bot = 1
result = None

a = GameResultState.WIN
b = GameResultState.DEFEAT
print(a is b)
print(a == b)
print(a == GameResultState.WIN)
if player > bot:
    result = GameResultState.WIN
else:
    result = GameResultState.DEFEAT

print(result)