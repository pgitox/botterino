from ..config import pg, username, debug, reddit, donotreply
from ..RedditPoller.RedditPoller import RedditPoller, CommentWrapper
from ..RedditPoller.Retry import retry
from geopy.point import Point
from geopy.distance import distance
from sty import fg
from random import randrange
from halo import Halo
import re
import requests
import json
import time
import warnings


decimal = re.compile("""([-+]?\d{1,2}[.]\d+),\s*([-+]?\d{1,3}[.]\d+)""")

# google maps decimal or dms
decimal_or_DMS = re.compile(
    """(?:((?:[-+]?\d{1,2}[.]\d+),\s*(?:[-+]?\d{1,3}[.]\d+))|(\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[N|S]\s\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[E|W]))"""
)

# google earth formats, other formats
everything_else = re.compile(
    """(^| )(-?\d{1,2}(\.\d+)?(?=\s*,?\s*)[\s,]+-?\d{1,3}(\.\d+)?|\d{1,2}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[NS](?=\s*,?\s*)[\s,]+\d{1,3}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[EW])"""
)

MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{},{}'

badColors = [0, 15, 16] + list(range(231,256))

def randomColorWithAuthor(author):
    color = abs(hash(author)) % 256
    while color in badColors:
        author += '*'
        color = abs(hash(author)) % 256
    return fg(color)

def randomColor():
    color = randrange(256)
    while color in badColors:
        color = randrange(256)
    return fg(color)

def postDelay():
    if debug:
        return -1

    r = requests.get('https://api.picturegame.co/current')
    data = json.loads(r.content)
    tries = 1

    while data['round']['hostName'].lower() != username.lower():
        tries += 1
        if tries > 5:
            return -1
        r = requests.get('https://api.picturegame.co/current')
        data = json.loads(r.content)
        time.sleep(5)

    return data['round'].get('postDelay', -1)

def getRoundPrefix():
    r = requests.get('https://api.picturegame.co/current')
    roundnum = int(json.loads(r.content)['round']['roundNumber']) + 1
    return f'[Round {roundnum}]'

def approved():
    c = next(iter(pg.contributor()))
    return c and c.name.lower() == username.lower()

@retry
@Halo(spinner='dots', color='yellow')
def waitForApproval():
    while not approved():
        continue

def getDistance(guess, answer):
    match = re.search(decimal_or_DMS, guess)
    if not match:
        match = re.search(everything_else, guess)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coord = Point(match[0]) if match else Point(guess)
    except ValueError as v:
        return
    try:
        return distance(coord, answer).m, coord
    except Exception as e:
        return


def getComments(submission):
    rp = RedditPoller(CommentWrapper(pg.comments, reddit.inbox.all))
    comments = rp.getLatest()
    # flush old comments
    while next(comments):
        continue

    for c in comments:
        if hasattr(c, 'submission') and hasattr(c, 'author') and c.author and c.submission:
            if c.author.name.lower() == username.lower() and '+correct' in c.body and not c.is_root:
                return
            if not c.is_root:
                continue
            if c.author.name.lower() in donotreply or c.submission != submission:
                continue
            yield c
