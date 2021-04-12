import praw
from sty import fg

debug = False

roundfile = 'Rounds/rounds.yaml'
archivefile = 'Rounds/archive.yaml'

reddit = praw.Reddit('botterino')
pg = reddit.subreddit('itoxtestingfacility' if debug else 'picturegame')

try:
    print(f'{fg.green}Successfully logged into reddit as {reddit.user.me()}')
except Exception as e:
    print(f'{fg.red}Unable to login to reddit. Please check praw.ini')
    print(f'{fg.red}{e}')

username = str(reddit.user.me())

donotreply = {
    'achievements-bot',
    username.lower(),
    'r-picturegame',
    'imreallycuriousbird',
}

incorrect = '❌'
