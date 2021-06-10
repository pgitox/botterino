import praw
import os
from . import botfiles
from sty import fg

debug = False
roundfile = botfiles.rounds
archivefile = botfiles.archive
cwd = os.getcwd()
try:
    os.chdir(botfiles.botconfig)
    reddit = praw.Reddit('botterino')
    print(f'{fg.green}Successfully logged into reddit as {reddit.user.me()}')
except Exception as e:
    print(f'{fg.red}Unable to login to reddit. Please check {botfiles.prawconfig}')
    print(f'{fg.red}{e}')
finally:
    os.chdir(cwd)

pg = reddit.subreddit('itoxtestingfacility' if debug else 'picturegame')

username = str(reddit.user.me())

donotreply = {
    'achievements-bot',
    username.lower(),
    'r-picturegame',
    'imreallycuriousbird',
}

incorrect = '❌'
