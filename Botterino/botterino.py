from .config import pg, username
from .posterino import submitRound
from .hosterino import checkAnswers
from .Utils.utils import waitForApproval, approved, postDelay, randomColor
from .Loader.loader import getRound
from sty import fg
from importlib.metadata import version
from update_checker import UpdateChecker
import time

v = version('botterino')
checker = UpdateChecker()
result = checker.check('botterino', v)
if result:
    print(f'{fg.yellow}{result}')
    print(f'{fg.yellow}run pip install --upgrade botterino to update')

def checkType(r):
    if 'tolerance' in r and 'answer' in r:
        return "automatic"
    if 'tolerances' in r and 'answers' in r:
        return "automatic"
    if 'manual' in r:
        return 'x wrong guesses, manual correct'
    return 'manual'

while True:
    print(f'{fg.yellow}Waiting for {username} to win a round... 🐌')
    waitForApproval()
    print(f'{fg.blue}Congrats on a well deserved win {username}! ⭐')
    r = getRound()
    while not r:
        print(f'{fg.red}No rounds in round file! checking again in 10s')
        time.sleep(10)
        r = getRound()
    submission = submitRound(r)
    print(f'{randomColor()}Your round was posted to https://reddit.com{submission.permalink}')
    print(f'{fg.magenta}Round \'{r["title"]}\' posted in {postDelay()}s')
    print(f'{fg.cyan}Checking Answers: {checkType(r)}...')
    checkAnswers(r, submission)
    while approved():
        continue
    after = r.get('after')
    if after:
        submission.reply(after)
        print(f'{randomColor()}Posted your message after the round: {after}')
