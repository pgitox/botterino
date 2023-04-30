from .hosterino import checkAnswers
from .config import pg
from .Utils.color import colormsg
from .Loader import loader
from sty import fg
import time

r = loader.getRound()
while not r:
    colormsg(f"No rounds in round file! checking again in 10s", fg.red)
    time.sleep(10)
    r = loader.getRound()

submission = next(iter(pg.new()))
colormsg(
    f"Checking answers on https://reddit.com{submission.permalink}",
)
checkAnswers(r, submission)
after = r.get("after")
if after:
    submission.reply(after)
