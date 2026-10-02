import re
import time
import traceback
from difflib import SequenceMatcher

from geopy.distance import distance
from geopy.point import Point
from sty import fg

from . import correctMessage, getBool, incorrectMessage
from .Loader.loader import loadHints
from .Map.map import Map
from .Utils.color import colormsg, getColorFromAuthor, hyperlink
from .Utils.utils import (
    MAPS_URL,
    decimal,
    getComments,
    getDistance,
    readExistingHints,
    safeReply,
)
from .validate import parsePoint


def withinTolerance(guess, answer, tolerance):
    return distance(guess, answer).m <= tolerance


def formatDistance(meters):
    if meters < 1000:
        return f"{round(meters, 2)}m"
    return f"{round(meters / 1000, 2)}km"


def commentLink(comment):
    return f"https://reddit.com{comment.permalink}"


def checkCoordinateMatch(points, answers, tolerances, used_points=None, depth=0):
    if used_points is None:
        used_points = [False] * len(points)

    if depth == len(points):
        return True

    for i in range(len(points)):
        if not used_points[i] and withinTolerance(
            points[i], answers[depth], tolerances[depth]
        ):
            used_points[i] = True
            if checkCoordinateMatch(
                points, answers, tolerances, used_points, depth + 1
            ):
                return True
            used_points[i] = False

    return False


def checkMultipleCoordinates(guess, answers, tolerances):
    guesser = guess.author.name
    answers = [parsePoint(a) for a in answers]
    points = [
        parsePoint(f"{lat},{lon}") for lat, lon in re.findall(decimal, guess.body)
    ]

    if (
        len(points) == len(answers)
        and None not in points
        and checkCoordinateMatch(points, answers, tolerances)
    ):
        colormsg(f"{guesser}'s guess {guess.body} was correct", fg.green)
        return True

    colormsg(f"{guesser}'s guess {guess.body} was incorrect", author=guesser)
    return False


def checkCoordinates(guess, answer, tolerance, map):
    guesser = guess.author.name
    answer = Point(answer)
    errorAndPoint = getDistance(guess.body, answer)
    if not errorAndPoint:
        colormsg(
            f"Could not find a coordinate in guess '{guess.body}' by {guesser}",
            author=guesser,
        )
        return "ignore"
    error, point = errorAndPoint
    error = round(error, 2)
    correct = error <= tolerance
    mapslink = MAPS_URL.format(point.latitude, point.longitude)
    color = fg.green if correct else getColorFromAuthor(guesser)
    link = commentLink(guess)
    colormsg(
        f'{guesser}\'s {hyperlink("guess", link)} was {formatDistance(error)} {hyperlink("off", mapslink)}',
        color,
    )

    if map:
        map.addPoint(point.latitude, point.longitude, guesser, error, link, correct)

    return correct


def checkText(guess, answer, tolerance, ignorecase):
    guesser = guess.author.name
    text = guess.body.strip().replace("\\", "")
    answer = str(answer).strip()

    if ignorecase:
        text, answer = text.lower(), answer.lower()

    similarity = SequenceMatcher(None, text, answer).ratio()
    colormsg(
        f"{guesser}'s guess was {round(similarity * 100, 3)}% similar to the correct answer",
        author=guesser,
    )
    return similarity >= tolerance


def postHint(submission, scheduled, hintText):
    if not hintText:
        colormsg(f"Skipping {scheduled}m hint: no text provided", fg.yellow)
        return
    hint = safeReply(submission, f"Hint({scheduled}m): {hintText}")
    if hint:
        colormsg(
            f"Posted hint ({scheduled}m) to https://reddit.com{hint.permalink}",
            fg.green,
        )


def checkHints(key, submission, round_over, poll_interval=30):
    """posts hints from hints.yaml on schedule until round_over is set"""
    posted_hints = set()
    while not round_over.is_set():
        try:
            existing_hints = None
            duration = int(time.time() - submission.created_utc) // 60
            for hint in loadHints(key):
                if not isinstance(hint, dict) or "time" not in hint:
                    continue
                hintId = (hint["time"], hint.get("text"))
                if hint["time"] > duration or hintId in posted_hints:
                    continue
                if existing_hints is None:
                    existing_hints = readExistingHints(submission)
                if hint.get("text") and any(
                    str(hint["text"]) in existing for existing in existing_hints
                ):
                    colormsg(
                        f"Looks like the hint for time {hint['time']}m is already posted"
                    )
                else:
                    postHint(submission, hint["time"], hint.get("text"))
                posted_hints.add(hintId)
        except Exception as e:  # pylint: disable=broad-except
            # e.g. hints.yaml is being edited, try again next time
            colormsg(f"Could not check hints: {type(e).__name__}: {e}", fg.yellow)

        round_over.wait(poll_interval)


def checkAnswer(
    comment,
    tolerance,
    text,
    answer,
    tolerances,
    answers,
    similarity,
    ignorecase,
    answerPlot,
):
    """
    returns True if the guess is correct, False if it is incorrect
    and None if there is nothing to check
    """
    result = True
    checked = False
    if tolerance is not None and answer is not None:
        r = checkCoordinates(comment, answer, float(tolerance), answerPlot)
        if r == "ignore":
            return False
        result = result and r
        checked = True
    elif tolerances and answers:
        tolerances = [float(t) for t in tolerances]
        if len(answers) != len(tolerances):
            colormsg(
                "Refusing to check answers, number of tolerances must equal number of answers.",
                fg.red,
            )
            return None
        result = result and checkMultipleCoordinates(comment, answers, tolerances)
        checked = True

    if text is not None and similarity is not None:
        if ignorecase is None:
            ignorecase = True
        result = checkText(comment, text, float(similarity), ignorecase) and result
        checked = True

    return result if checked else None


def roundFields(r):
    return (
        r.get("tolerance"),
        r.get("manual"),
        r.get("text"),
        r.get("answer"),
        r.get("tolerances"),
        r.get("answers"),
        r.get("similarity"),
        r.get("ignorecase"),
    )


def reportResult(c, result, manual):
    """replies to a checked guess, returns True if the guess was corrected"""
    if result is None:
        return False
    if not result:
        safeReply(c, incorrectMessage)
        return False
    if manual:
        colormsg(
            f"Guess '{c.body}' looks correct, but you will have to check it out: {commentLink(c)}",
            fg.green,
        )
        return False
    plusCorrect = safeReply(c, correctMessage)
    if not plusCorrect:
        colormsg(
            f"Could not +correct {c.author.name}, please do it yourself: {commentLink(c)}",
            fg.red,
        )
        return False
    colormsg(
        f"Corrected {c.author.name} in {round(plusCorrect.created_utc - c.created_utc)}s 🎉",
        fg.green,
    )
    return True


def makeMap(key, r):
    """a map to plot guesses on, or None if the round has no single coordinate answer"""
    if not getBool("save_map"):
        return None
    point = parsePoint(r.get("answer"))
    if point is None or r.get("tolerance") is None:
        return None
    try:
        return Map(point.latitude, point.longitude, float(r["tolerance"]), key)
    except Exception as e:  # pylint: disable=broad-except
        colormsg(f"Could not create a map of guesses: {e}", fg.yellow)
        return None


def checkAnswers(r, submission, key="round", skip=()):
    (
        tolerance,
        manual,
        text,
        answer,
        tolerances,
        answers,
        similarity,
        ignorecase,
    ) = roundFields(r)

    answerPlot = makeMap(key, r)
    if answerPlot:
        colormsg(f"Guesses will be plotted at {answerPlot.getFilePath()}", fg.cyan)

    for c in getComments(submission, skip):
        if tolerance is None and not tolerances and not (text and similarity):
            continue
        try:
            result = checkAnswer(
                c,
                tolerance,
                text,
                answer,
                tolerances,
                answers,
                similarity,
                ignorecase,
                answerPlot,
            )
            if reportResult(c, result, manual):
                break
        except Exception:  # pylint: disable=broad-except
            # one bad comment should never stop the bot from hosting
            colormsg(f"Error checking {commentLink(c)}:", fg.red)
            colormsg(traceback.format_exc(), fg.red)

    if answerPlot and answerPlot.getFilePath():
        colormsg(
            f"Answers to your round plotted at {answerPlot.getFilePath()}", fg.cyan
        )
        if getBool("open_map"):
            answerPlot.openMapInBrowser()
