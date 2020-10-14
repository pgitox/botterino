import praw

# fill in the below 5 None values
# See readme for instructions
# values must be in quotes
# eg: username = 'ItoXICI'

client_secret = None
client_id = None
username = None
password = None
user_agent = None

roundfile = "rounds/rounds.yaml"
archivefile = "rounds/archive.yaml"

debug = False

# set to True if you use 2fa
two_factor = False
pw_suffix = ''

if two_factor:
    pw_suffix = ':' + input("Enter 2fa code: ")

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
    username=username,
    password=password + pw_suffix,
)

pg = reddit.subreddit('itoxtestingfacility' if debug else 'picturegame')


donotreply = {
    'achievements-bot',
    username.lower(),
    'r-picturegame',
    'imreallycuriousbird',
}

incorrect = '❌'
