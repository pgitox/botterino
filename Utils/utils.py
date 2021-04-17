from config import pg, username, debug 
from RedditPoller.Retry import retry
from geopy.point import Point
from geopy.distance import distance
from sty import fg
from random import choice
import re
import requests
import json
import time

decimal = re.compile("""([-+]?\d{1,2}[.]\d+),\s*([-+]?\d{1,3}[.]\d+)""")

# google maps decimal or dms
decimal_or_DMS = re.compile(
    """(?:((?:[-+]?\d{1,2}[.]\d+),\s*(?:[-+]?\d{1,3}[.]\d+))|(\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[N|S]\s\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[E|W]))"""
)

# google earth formats, other formats
everything_else = re.compile(
    """(^| )(-?\d{1,2}(\.\d+)?(?=\s*,?\s*)[\s,]+-?\d{1,3}(\.\d+)?|\d{1,2}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[NS](?=\s*,?\s*)[\s,]+\d{1,3}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[EW])"""
)

colors = [
    fg.red,
    fg.green,
    fg.yellow,
    fg.blue,
    fg.magenta,
    fg.cyan,
    fg.li_grey,
    fg.rs,
    fg.da_grey,
    fg.li_red,
    fg.li_green,
    fg.li_yellow,
    fg.li_blue,
    fg.li_magenta,
    fg.li_cyan,
    fg.white
]

def randomColor():
    return choice(colors)

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
def waitForApproval():
    while not approved():
        continue

def getDistance(guess, answer):
    match = re.search(decimal_or_DMS, guess)
    if not match:
        match = re.search(everything_else, guess)
    try:
        coord = Point(match[0]) if match else Point(guess)
    except ValueError as v:
        print(f'{fg.red}There was a problem in getting distance: for guess {guess}{v}')

    try:
        return distance(coord, answer).m
    except Exception as e:
        print(f'{fg.red}There was a problem in getting distance for guess {guess}: {e}')


def getComments(rp):
    # flush old comments
    while next(rp):
        continue

    while True:
        c = next(rp)
        if hasattr(c, 'submission') and hasattr(c, 'author'):
            yield c
