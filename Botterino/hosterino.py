from geopy.distance import distance
from geopy.point import Point
from .config import donotreply, incorrect, reddit, username, pg
from itertools import permutations
import re
from sty import fg
from .Utils.utils import decimal, getComments, getDistance, randomColor, randomColorWithAuthor
from difflib import SequenceMatcher

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
    error = getDistance(guess.body, answer)
    if error is None:
        print(f"{randomColorWithAuthor(guesser)}Could not find a coordinate in guess '{guess.body}' by {guesser}")
        return 'ignore'
    error = round(error, 2)
    print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess {guess.body[:120]} was {error} meters off')
    return error <= tolerance

def checkText(guess, answer, tolerance, ignorecase):
    guesser = guess.author.name
    text = guess.body.strip().replace('\\', '')

    if not ignorecase:
        text,answer = text.lower(), answer.lower()

    similarity = SequenceMatcher(None, text, answer).ratio()
    print(f'{randomColorWithAuthor(guesser)}{guesser}\'s guess was {round(similarity, 3)}% similar to the correct answer')
    return similarity >= tolerance

def checkAnswers(r, submission):
    tolerance, manual, after, text, answer, tolerances, answers, similarity, ignorecase = float(
        r.get('tolerance', 0)), r.get('manual'), r.get('after'), r.get(
            'text'), r.get('answer'), r.get('tolerances'), r.get(
                'answers'), r.get('similarity'), r.get('ignorecase')

    if not tolerance and not tolerances and not text:
        return

    for c in getComments(submission):
        result = True
        if tolerance:
            r = checkCoordinates(c, answer, tolerance)
            if r == 'ignore':
                continue
            result = result and r
        elif tolerances:
            tolerances = [float(t) for t in r['tolerances']]
            if len(answers) != len(tolerances):
                print('{fg.red}Refusing to check answers, number of tolerances must equal number of answers.')
            result = result and checkMultipleCoordinates(c, answers, tolerances)

        if text and not similarity:
            similarity = 1.0

        if not ignorecase:
            ignorecase = True

        if text:
            result = result and checkText(c, text, similarity, ignorecase)

        if not result:
            c.reply(incorrect)
        if result:
            if manual:
                print(f"{randomColor()}Guess '{c.body}' looks correct, but you will have to check it out.")
            else:
                plusCorrect = c.reply('+correct')
                guesser = c.author.name
                print(
                    f'{randomColorWithAuthor(guesser)}Corrected {guesser} in {plusCorrect.created_utc - c.created_utc}s')
                break
