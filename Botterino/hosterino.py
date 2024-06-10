from geopy.distance import distance
from geopy.point import Point
from .config import (
    correctMessage,
    incorrectMessage,
    botfiles,
)
from itertools import permutations
import re
from sty import fg
from .Utils.color import colormsg, getColorFromAuthor
from .Utils.utils import (
    approved,
    decimal,
    getComments,
    getDistance,
    MAPS_URL,
    hyperlink,
)
from difflib import SequenceMatcher
from .Map.map import Map
import time


def withinTolerance(guess, answer, tolerance):
    return distance(guess, answer).m <= tolerance


def checkCoordinateMatch(points, answers, tolerances, used_points=None, depth=0):
    if used_points is None:
        used_points = [False] * len(points)

    if depth == len(points):
        return True

    for i in range(len(points)):
        if not used_points[i] and withinTolerance(points[i], answers[depth], tolerances[depth]):
            used_points[i] = True
            if checkCoordinateMatch(points, answers, tolerances, used_points, depth + 1):
                return True
            used_points[i] = False

    return False


def checkMultipleCoordinates(guess, answers, tolerances):
    guesser = guess.author.name
    answers = [Point(a) for a in answers]
    match = re.findall(decimal, guess.body)

    if len(match) != len(answers):
        colormsg(f"{guesser}'s guess {guess.body} was incorrect", author=guesser)
        return False

    points = [Point(f"{lat},{lon}") for lat, lon in match]

    if checkCoordinateMatch(points, answers, tolerances):
        return True
    else:
        colormsg(f"{guesser}'s guess {guess.body} was incorrect", author=guesser)
        return False


def checkCoordinates(guess, answer, tolerance, map):
    guesser = guess.author.name
    answer = Point(answer)
    errorAndPoint = getDistance(guess.body, answer)
    error, point = errorAndPoint if errorAndPoint else (None, None)
    if error is None:
        colormsg(
            f"Could not find a coordinate in guess '{guess.body}' by {guesser}",
            author=guesser,
        )
        return "ignore"
    error = round(error, 2)
    mapslink = MAPS_URL.format(point.latitude, point.longitude)
    color = fg.green if error <= tolerance else getColorFromAuthor(guesser)
    pl = ""
    if hasattr(guess, "context"):
        pl = guess.context
    elif hasattr(guess, "permalink"):
        pl = guess.permalink
    commentLink = f"https://reddit.com{pl}"
    if error < 1000:
        colormsg(
            f'{guesser}\'s {hyperlink("guess", commentLink)} was {error}m {hyperlink("off", mapslink)}',
            color,
        )
    else:
        colormsg(
            f'{guesser}\'s {hyperlink("guess", commentLink)} was {round(error/1000,2)}km {hyperlink("off", mapslink)}',
            color,
        )

    if map:
        # TODO: try to give different users differnt colors
        map.addPoint(
            point.latitude,
            point.longitude,
            guesser,
            error,
            commentLink,
            "red" if error > tolerance else "green",
        )

    return error <= tolerance


def checkText(guess, answer, tolerance, ignorecase):
    guesser = guess.author.name
    text = guess.body.strip().replace("\\", "")

    if ignorecase:
        text, answer = text.lower(), answer.lower()

    similarity = SequenceMatcher(None, text, answer).ratio()
    colormsg(
        f"{guesser}'s guess was {round(similarity * 100, 3)}% similar to the correct answer",
        author=guesser,
    )
    return similarity >= tolerance


def postHint(submission, time):
    with open(botfiles.hintfile, "r") as F:
        hintText = F.read()
    if not hintText:
        colormsg(f"Skipping {time}m hint: hints.txt is empty", fg.yellow)
        return
    hint = submission.reply(f"Hint({time}m): {hintText}")
    colormsg(f"Posted hint ({time}m) to https://reddit.com{hint.permalink}", fg.green)
    open(botfiles.hintfile, "w").close()


def checkHints(hints, submission):
    hints = list(hints)
    hints += [60, 120, 180, 240]
    hints = sorted(list(set(hints)))
    while hints and approved():
        top = hints[0]
        duration = int(time.time() - submission.created_utc)
        duration = duration // 60
        if duration >= top:
            postHint(submission, duration)
            hints.pop(0)
        time.sleep(10)
        pass


def checkAnswers(r, submission):
    (
        tolerance,
        manual,
        text,
        answer,
        tolerances,
        answers,
        similarity,
        ignorecase,
    ) = (
        r.get("tolerance"),
        r.get("manual"),
        r.get("text"),
        r.get("answer"),
        r.get("tolerances"),
        r.get("answers"),
        r.get("similarity"),
        r.get("ignorecase"),
    )

    answerPlot = None
    if answer and tolerance and not answers:
        try:
            answerPoint = Point(answer)
            answerPlot = Map(answerPoint.latitude, answerPoint.longitude)
        except Exception:
            pass

    if tolerance is None and tolerances is None and text is None:
        return

    for c in getComments(submission):
        result = True
        if tolerance is not None:
            tolerance = float(tolerance)
            r = checkCoordinates(c, answer, tolerance, answerPlot)
            if r == "ignore":
                continue
            result = result and r
        elif tolerances:
            tolerances = [float(t) for t in r["tolerances"]]
            if len(answers) != len(tolerances):
                colormsg(
                    f"Refusing to check answers, number of tolerances must equal number of answers.",
                    fg.red
                )
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
                colormsg(
                    f"Guess '{c.body}' looks correct, but you will have to check it out.",
                )
            else:
                plusCorrect = c.reply(correctMessage)
                guesser = c.author.name
                colormsg(
                    f"Corrected {guesser} in {plusCorrect.created_utc - c.created_utc}s",
                    fg.green,
                )
                break

    # TODO: show the map on every guess instead of only when the round is over
    if answerPlot:
        answerPlot.saveMap()
        outputFile = answerPlot.getFilePath()
        if outputFile:
            colormsg(f"Answers to your round plotted at {outputFile}", fg.cyan)
            answerPlot.openMapInBrowser()
