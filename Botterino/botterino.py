from .config import pg, username, hints
from .posterino import submitRound
from .hosterino import checkAnswers, checkHints
from .Utils.utils import waitForApproval, approved, postDelay, randomColor
from .Loader.loader import getRound
from sty import fg
from importlib.metadata import version
from update_checker import UpdateChecker
from threading import Thread
import time

v = version('botterino')
checker = UpdateChecker()
result = checker.check('botterino', v)
if result:
    print(f'{fg.yellow}{result}')
    print(f'{fg.yellow}run "pip install --upgrade botterino" to update')

def checkType(r):
    types = []
    if 'tolerance' in r and 'answer' in r:
        types.append('coordinates')
    if 'tolerances' in r and 'answers' in r:
        types.append('multiple coordinates')
    if 'text' in r and 'similarity' in r:
        types.append('text match')
    if 'manual' in r:
        types.append('x wrong guesses with manual correct')
    if not types:
        return 'no automatic replies'
    if 'manual' not in r:
        types.append('automatic')
    return ','.join(types)

def main(stop=None):
    while True:
        print(f'{fg.yellow}Waiting for {username} to win a round... 🐌', end=f'{fg.rs}\n')
        stopped = waitForApproval(stop)
        if stopped or stop:
            print(f'{fg.red}Stopped botterino{fg.rs}')
            return
        print(f'{fg.blue}Congrats on a well deserved win {username}! ⭐', end=f'{fg.rs}\n')
        r = getRound()
        while not r:
            print(f'{fg.red}No rounds in round file! checking again in 10s')
            time.sleep(10)
            r = getRound()
        submission = submitRound(r)
        print(f'{randomColor()}Your round was posted to https://reddit.com{submission.permalink}', end=f'{fg.rs}\n')
        print(f'{fg.magenta}Round \'{r["title"]}\' posted in {postDelay()}s', end=f'{fg.rs}\n')
        print(f'{fg.cyan}Checking Answers: {checkType(r)}...{fg.rs}', end=f'{fg.rs}\n')
        H = hints if not r.get('hints') else r.get('hints')
        CheckAnswers = Thread(target=checkAnswers, args=(r, submission))
        CheckHints = Thread(target=checkHints, args=(H, submission))
        CheckAnswers.start()
        CheckHints.start()
        CheckAnswers.join()
        CheckHints.join()
        while approved():
            continue
        after = r.get('after')
        if after:
            submission.reply(after)
            print(f'{randomColor()}Posted your message after the round: {after}', end=f'{fg.rs}\n')
