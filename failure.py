from Botterino.hosterino import checkAnswers
from config import pg
from Utils.utils import randomColor

# change these three lines as appropriate
answer = 41.170280504136485, 72.39233446994774
tolerance = 20
manual = False

r = {
    "answer" : answer,
    "tolerance": tolerance,
    "manual": manual
}

submission = next(iter(pg.new()))
print(f'{randomColor()}Checking answers on https://reddit.com{submission.permalink}')
checkAnswers(r, submission)