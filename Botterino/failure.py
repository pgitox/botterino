from .hosterino import checkAnswers
from .config import pg
from .Utils.utils import randomColor
from .Loader import loader
from sty import fg
import time


r = loader.getRound()
while not r:
    print(f'{fg.red}No rounds in round file! checking again in 10s')
    time.sleep(10)
    r = loader.getRound()

submission = next(iter(pg.new()))
print(f'{randomColor()}Checking answers on https://reddit.com{submission.permalink}')
checkAnswers(r, submission)
after = r.get('after')
if after:
    submission.reply(after)