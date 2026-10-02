import re
import sys
import time
import warnings

import requests
from geopy.distance import distance
from geopy.point import Point
from halo import Halo
from praw.exceptions import RedditAPIException
from prawcore.exceptions import PrawcoreException
from requests.exceptions import RequestException
from sty import fg

from .. import correctMessage
from ..config import pg, username, debug, reddit, donotreply, api
from ..RedditPoller.RedditPoller import RedditPoller
from ..RedditPoller.Retry import retry
from .color import colormsg, useColor

decimal = re.compile(r"""([-+]?\d{1,2}[.]\d+),\s*([-+]?\d{1,3}[.]\d+)""")

# google maps decimal or dms
decimal_or_DMS = re.compile(
    r"""(?:((?:[-+]?\d{1,2}[.]\d+),\s*(?:[-+]?\d{1,3}[.]\d+))|(\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[N|S]\s\d{1,3}°\d{1,3}'\d{1,3}\.\d\"[E|W]))"""
)

# google earth formats, other formats
everything_else = re.compile(
    r"""(^| )(-?\d{1,2}(\.\d+)?(?=\s*,?\s*)[\s,]+-?\d{1,3}(\.\d+)?|\d{1,2}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[NS](?=\s*,?\s*)[\s,]+\d{1,3}(\.\d+°|°(\d{1,2}(\.\d+'|'(\d{1,2}(\.\d+)?\")?))?)[EW])"""
)

roundNumber = re.compile(r"\[Round\s*(\d+)\]", re.IGNORECASE)

MAPS_URL = "https://maps.google.com/maps?t=k&q=loc:{},{}"

HEADERS = {"User-Agent": "botterino (https://github.com/pgitox/botterino)"}

# seconds between checks for approval to post
APPROVAL_POLL_SECONDS = 0.5


@retry
def mySubmissions(limit=200):
    """returns a list of the user's submissions to pg, newest first"""
    return [
        s
        for s in reddit.user.me().submissions.new(limit=limit)
        if s.subreddit.display_name.lower() == pg.display_name.lower()
    ]


def submissions():
    """
    returns a generator of titles of submissions to pg
    newest submissions first
    """
    for submission in mySubmissions() or []:
        yield submission.title


def latestSubmission():
    """the user's most recent submission to pg"""
    return next(iter(mySubmissions(limit=25) or []), None)


def currentRound(attempts=5):
    """the current round from the picturegame api, or None if the api cannot be reached"""
    for attempt in range(attempts):
        try:
            r = requests.get(f"{api}/current", headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r.json()["round"]
        except (RequestException, ValueError, KeyError, TypeError) as e:
            if attempt == attempts - 1:
                colormsg(f"Could not reach the picturegame api: {e}", fg.yellow)
            else:
                time.sleep(2)
    return None


def postDelay():
    if debug:
        return -1

    for _ in range(5):
        data = currentRound(attempts=1)
        if data and str(data.get("hostName", "")).lower() == username.lower():
            return data.get("postDelay", -1)
        time.sleep(5)
    return -1


@retry
def _latestRoundNumberFromReddit():
    numbers = []
    for s in pg.new(limit=10):
        match = roundNumber.search(s.title)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) if numbers else None


def getRoundPrefix():
    data = currentRound()
    if data and data.get("roundNumber"):
        return f"[Round {int(data['roundNumber']) + 1}]"
    # fall back to the newest round posted to the subreddit
    latest = _latestRoundNumberFromReddit()
    if latest:
        return f"[Round {latest + 1}]"
    raise RuntimeError("Could not figure out the round number")


@retry
def approved():
    c = next(iter(pg.contributor(limit=1)), None)
    return bool(c) and c.name.lower() == username.lower()


def waitForApproval(stop=None, onTick=None, tickSeconds=5):
    """
    blocks until the user is approved to post, returns True if stopped instead
    onTick(spinner) is called every tickSeconds while waiting
    """
    spinner = Halo(
        spinner="dots",
        color="yellow" if useColor else None,
        stream=sys.stdout,
        enabled=sys.stdout.isatty(),
    )
    spinner.start()
    lastTick = time.time()
    try:
        while not stop:
            if approved():
                return False
            if onTick and time.time() - lastTick >= tickSeconds:
                lastTick = time.time()
                onTick(spinner)
            time.sleep(APPROVAL_POLL_SECONDS)
        return True
    finally:
        spinner.stop()


def waitWhileApproved(stop=None):
    """blocks until somebody else is approved to post"""
    while not stop and approved():
        time.sleep(2)


def getDistance(guess, answer):
    match = re.search(decimal_or_DMS, guess)
    if not match:
        match = re.search(everything_else, guess)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coord = Point(match[0]) if match else Point(guess)
        return distance(coord, answer).m, coord
    except (ValueError, TypeError):
        return None


def isCorrection(comment, submission):
    """whether the comment is the host's +correct on the round"""
    body = comment.body.lower()
    return (
        comment.author.name.lower() == username.lower()
        and not comment.is_root
        and comment.submission == submission
        and (correctMessage.strip().lower() in body or "+correct" in body)
    )


def getComments(submission, skip=()):
    """
    yields new top level comments on submission, oldest first, except the ids in skip
    returns once the host replies with +correct
    """
    # comments on the host's own submission also show up in the inbox, which catches
    # comments the subreddit listing misses
    rp = RedditPoller(pg.comments, reddit.inbox.all)
    for c in rp.getLatest():
        if not c or not hasattr(c, "submission") or not c.author:
            continue
        if c.created_utc < submission.created_utc:
            continue
        if isCorrection(c, submission):
            return
        if not c.is_root:
            continue
        if c.author.name.lower() in donotreply or c.submission != submission:
            continue
        if c.id in skip:
            continue
        yield c


@retry
def getCurrentComments(submission):
    refreshed = reddit.submission(id=submission.id)
    refreshed.comments.replace_more(limit=None)
    return refreshed.comments.list()


def readExistingHints(submission):
    existing_hints = []
    for c in getCurrentComments(submission) or []:
        if c.author and c.author.name.lower() == username.lower() and "Hint" in c.body:
            existing_hints.append(c.body)
    return existing_hints


def hasHostReplied(comment):
    for reply in comment.replies:
        if reply.author and reply.author.name.lower() == username.lower():
            return True
    return False


def safeReply(target, body, attempts=5):
    """
    reply to a comment or submission without crashing the bot
    returns the reply, or None if it could not be posted
    """
    for attempt in range(attempts):
        try:
            return target.reply(body)
        except RedditAPIException as e:
            if any(item.error_type == "RATELIMIT" for item in e.items):
                colormsg(f"Reddit rate limit hit, waiting to reply: {e}", fg.yellow)
                time.sleep(15)
                continue
            # deleted or locked comments etc, retrying will not help
            colormsg(
                f"Could not reply to {getattr(target, 'permalink', target)}: {e}",
                fg.red,
            )
            return None
        except (PrawcoreException, RequestException) as e:
            colormsg(
                f"Could not reach reddit to reply ({type(e).__name__}), retrying",
                fg.yellow,
            )
            time.sleep(5 * (attempt + 1))
    colormsg(
        f"Giving up replying '{body}' to {getattr(target, 'permalink', target)}", fg.red
    )
    return None
