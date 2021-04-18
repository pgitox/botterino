from RedditPoller.RedditPoller import RedditPoller, CommentWrapper
from geopy.distance import distance
from geopy.point import Point
from config import donotreply, incorrect, reddit, username, pg
from itertools import permutations
import re
from sty import fg
from Utils.utils import decimal, getComments, getDistance, randomColor


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
    for c in getComments(comments.getLatest()):
        if c.author.name.lower() == username.lower() and '+correct' in c.body:
            return

        if not c.is_root:
            continue

        if c.author.name.lower() in donotreply or c.submission != submission:
            continue

        error = getDistance(c.body, answer) if not multiple else None
        is_coord = error is not None

        if multiple:
            correct = check_multiple(c.body, answer, tolerance)
        else:
            correct = is_coord and error <= tolerance

        if correct and not manual:
            plus_correct = c.reply('+correct')
        elif is_coord and not correct or not correct and multiple:
            c.reply(incorrect)

        error = round(error, 2)
        print(f'{randomColor()}{c.author}\'s guess {c.body} was {error} meters off')

        if correct and not manual:
            print(
                f'{randomColor()}corrected {c.author} in {plus_correct.created_utc - c.created_utc}s'
            )
        if correct and not manual:
            return

def checkAnswers(r, submission):
    after = r.get('after')
    if 'tolerance' in r:
        answer = r['answer']
        tolerance = float(r['tolerance'])
        manual = r.get('manual', False)
        check(submission, answer, tolerance, manual)
    elif 'tolerances' in r:
        answer = r['answers']
        tolerance = [float(t) for t in r['tolerances']]
        if len(answer) != len(tolerance):
            print('{fg.red}Refusing to check answers, number of tolerances must equal number of answers.') 
        manual = r.get('manual', False)
        check(submission, answer, tolerance, manual, multiple=True)

    if after:
        submission.reply(after)
        print(f'{randomColor()}Posted your message after the round: {after}')

