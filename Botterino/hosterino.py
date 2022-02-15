from geopy.distance import distance
from geopy.point import Point
from .config import donotreply, correctMessage, incorrectMessage, reddit, username, pg, botfiles
from itertools import permutations
import re
from sty import fg
from .Utils.utils import decimal, getComments, getDistance, randomColor, randomColorWithAuthor, MAPS_URL
from difflib import SequenceMatcher
import time

def withinTolerance(guess, answer, tolerance):
    return distance(guess, answer).m <= tolerance

def checkMultipleCoordinates(guess, answers, tolerances):
    guesser = guess.author.name
    answers = [Point(a) for a in answers]
    match = re.findall(decimal, guess.body)
    if len(match) != len(answers):
        # TODO print a message here
        print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess {guess.body} was incorrect')
        return False
    try:
        points = [Point(f'{lat},{lon}') for lat, lon in match]
        points = permutations(points)
    except Exception as e:
        print(f'{randomColor()}Something happened: ', e, 'it probably does not matter')
        return False

    results = [[withinTolerance(p, a, t) for p, a, t in zip(ps, answers, tolerances)] for ps in points]
    results = [all(r) for r in results]
    result = any(results)
    if not result:
        print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess {guess.body} was incorrect')
    return result

def checkCoordinates(guess, answer, tolerance):
    guesser = guess.author.name
    answer = Point(answer)
    errorAndPoint = getDistance(guess.body, answer)
    error, point = errorAndPoint if errorAndPoint else (None, None)
    if error is None:
        print(f"{randomColorWithAuthor(guesser)}Could not find a coordinate in guess '{guess.body}' by {guesser}")
        return 'ignore'
    error = round(error, 2)
    mapslink = MAPS_URL.format(point.latitude, point.longitude)
    print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess {mapslink} was {error} meters off')
    return error <= tolerance

def checkText(guess, answer, tolerance, ignorecase):
    guesser = guess.author.name
    text = guess.body.strip().replace('\\', '')

    if ignorecase:
        text,answer = text.lower(), answer.lower()

    similarity = SequenceMatcher(None, text, answer).ratio()
    print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess was {round(similarity * 100, 3)}% similar to the correct answer')
    return similarity >= tolerance

def postHint(submission, time):
    with open(botfiles.hintfile, 'r') as F:
        hintText = F.read()
    if not hintText:
        print(f'{fg.yellow}Skipping {time}m hint: hintfile is empty')
        return
    hint = submission.reply(f'Hint({time}m): {hintText}')
    print(f'{fg.green}Posted hint ({time}m) to https://reddit.com{hint.permalink}')
    open(botfiles.hintfile, 'w').close()

def checkHints(hints, submission):
    hints = list(hints)
    hints += [60, 120, 180, 240]
    hints = sorted(list(set(hints)))
    while hints:
        if not submission.link_flair_text:
            continue
        if 'UNSOLVED' not in submission.link_flair_text:
            return
        top = hints[0]
        duration = int(time.time() - submission.created_utc)
        duration = duration//60
        if duration >= top:
            postHint(submission, duration)
            hints.pop(0)
        time.sleep(10)
        pass

def checkAnswers(r, submission):
    tolerance, manual, text, answer, tolerances, answers, similarity, ignorecase, hints, = r.get(
        'tolerance'), r.get('manual'), r.get('text'), r.get(
            'answer'), r.get('tolerances'), r.get('answers'), r.get(
                'similarity'), r.get('ignorecase'), r.get('hints', [])

    if tolerance is None and tolerances is None and text is None:
        return

    for c in getComments(submission):
        result = True
        if tolerance:
            tolerance = float(tolerance)
            r = checkCoordinates(c, answer, tolerance)
            if r == 'ignore':
                continue
            result = result and r
        elif tolerances:
            tolerances = [float(t) for t in r['tolerances']]
            if len(answers) != len(tolerances):
                print('{fg.red}Refusing to check answers, number of tolerances must equal number of answers.')
            result = result and checkMultipleCoordinates(c, answers, tolerances)

        if text and similarity is None:
            continue

        if ignorecase is None:
            ignorecase = True

        if text:
            result = result and checkText(c, text, similarity, ignorecase)

        if not result:
            c.reply(incorrectMessage)
        if result:
            if manual:
                print(f"{randomColor()}Guess '{c.body}' looks correct, but you will have to check it out.")
            else:
                plusCorrect = c.reply(correctMessage)
                guesser = c.author.name
                print(
                    f'{randomColorWithAuthor(guesser)}Corrected {guesser} in {plusCorrect.created_utc - c.created_utc}s')
                break
