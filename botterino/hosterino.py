from re import L
from RedditPoller.RedditPoller import RedditPoller, CommentWrapper
from geopy.distance import distance
from geopy.point import Point
from config import donotreply, incorrect, reddit, username, pg
from itertools import permutations
import re


decimal = re.compile("""([-+]?\d{1,2}[.]\d+),\s*([-+]?\d{1,3}[.]\d+)""")

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
    try:
        coord = Point(match[0]) if match else Point(guess)
    except ValueError as v:
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


def check_helper(guess, answer, tolerance):
    return distance(guess, answer).m <= tolerance


def check_multiple(guess, answers, tolerances):
    match = re.findall(decimal, guess)
    if len(match) != len(answers):
        return False
    try:
        points = [Point(f'{lat},{lon}') for lat, lon in match]
        points = permutations(points)
    except Exception as e:
        print('Something happened: ', e, 'it probably does not matter')
        return False

    results = [[check_helper(p, a, t) for p, a, t in zip(ps, answers, tolerances)] for ps in points]
    results = [all(r) for r in results]
    return any(results)


def check(submission, answer, tolerance, manual=False, multiple=False):
    comments = RedditPoller(CommentWrapper(pg.comments, reddit.inbox.all))
    if not multiple:
        answer = Point(answer)
    else:
        answer = [Point(a) for a in answer]
    plus_correct = None
    for c in get_comments(comments.getLatest()):
        if c.author.name.lower() == username.lower() and '+correct' in c.body:
            return

        if not c.is_root:
            continue

        if c.author.name.lower() in donotreply or c.submission != submission:
            continue

        error = get_distance(c.body, answer) if not multiple else None
        is_coord = error is not None

        if multiple:
            correct = check_multiple(c.body, answer, tolerance)
        else:
            correct = is_coord and error <= tolerance

        if correct and not manual:
            plus_correct = c.reply('+correct')
        elif is_coord and not correct or not correct and multiple:
            c.reply(incorrect)

        print(f'{c.author}\'s guess {c.body} was {error} meters off')

        if correct and not manual:
            print(
                f'corrected {c.author} in {plus_correct.created_utc - c.created_utc}s'
            )
        if correct and not manual:
            return
