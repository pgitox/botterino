from config import pg, username
from sty import fg
from Utils.utils import waitForApproval, approved, postDelay, randomColor
from Utils import update
from Loader.loader import getRound
from Botterino.posterino import submitRound
from Botterino.hosterino import checkAnswers
import time 
import configparser

def checkType(r):
    if 'tolerance' in r and 'answer' in r:
        return "automatic"
    if 'manual' in r:
        return 'x wrong guesses, manual correct'
    return 'manual'

parser = configparser.ConfigParser()
parser.read('praw.ini')
if not parser['botterino'].get('donotupdate'):
    print(f'{fg.cyan}Checking for updates...')
    if update.hasUpdate():
        doUpdate = input(f'{fg.green}There is an update available! Would you like to update? Enter Y/N ').lower() == 'y'
        if doUpdate:
            update.doUpdate()
            print(f'{fg.green}Successfully updated. Please restart botterino')
            exit(0)
    else:
        print(f'{fg.yellow}You are up to date!')

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
