from config import pg, username
from sty import fg
from Utils.utils import waitForApproval, approved, postDelay, randomColor
from Loader.loader import getRound
from Botterino.posterino import submitRound
from Botterino.hosterino import checkAnswers
import time 

def checkType(r):
    if 'tolerance' in r and 'answer' in r:
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
