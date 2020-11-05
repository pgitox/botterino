from RedditPoller.RedditPoller import RedditPoller
from geopy.distance import distance
from geopy.point import Point
from config import donotreply, incorrect, reddit, username
import re

comments = RedditPoller(reddit.inbox.all)

# google maps decimal or dms
decimal_or_DMS = re.compile(
    """(?:((?:[-+]?\d{1,2}[.]\d+),\s*(?:[-+]?\d{1,3}[.]\d+))|(\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[N|S]\s\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[E|W]))"""
)

# google earth formats, other formats
everything_else = re.compile(
    """(^| )(-?\d{1,2}(\.\d+)?(?=\s*,?\s*)[\s,]+-?\d{1,3}(\.\d+)?|\d{1,2}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[NS](?=\s*,?\s*)[\s,]+\d{1,3}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[EW])"""
)


def get_distance(guess, answer):
    match = re.search(decimal_or_DMS, guess)
    if not match:
        match = re.search(everything_else, guess)
        if not match:
            return
    try:
        coord = Point(match[0])
    except ValueError as v:
        print('something happened:', v) 
        return
    try:
        return distance(coord, answer).m
    except Exception as e:
        print('There was a problem in getting distance', e)


def get_comments(rp):
    # flush old comments
    while next(rp):
        continue

    while True:
        c = next(rp)
        if hasattr(c, 'submission'):
            yield c


def check(submission, answer, tolerance, manual=False):
    answer = Point(answer)
    plus_correct = None
    for c in get_comments(comments.getLatest()):
        if c.author.name.lower() == username.lower() and '+correct' in c.body:
            return
        if (c.author.name.lower() not in donotreply
                and c.submission == submission):
            error = get_distance(c.body, answer)
            is_coord = error is not None
            correct = is_coord and error <= tolerance
            if correct and not manual:
                plus_correct = c.reply('+correct')
            elif is_coord and not correct:
                c.reply(incorrect)
            print(f'{c.author}\'s guess {c.body} was {error} meters off')
            if correct and not manual:
                print(
                    f'corrected {c.author} in {plus_correct.created_utc - c.created_utc}s'
                )
            if is_coord and correct and not manual:
                return
