import re
import time

from praw.exceptions import WebSocketException
from sty import fg

from .config import pg
from .Loader.loader import resolveImagePath
from .Utils.color import colormsg
from .Utils.utils import getRoundPrefix, latestSubmission, safeReply, submissions

# seconds to wait before posting a round's message, so it appears below the round bot's comment
MESSAGE_DELAY = 15


def getSeriesPrefix(name):
    if not name:
        return ""
    name = str(name).strip()
    escaped = re.escape(name)
    indefinite = re.compile(rf"\s*{escaped}\s*#?\s*(\d+)\s*", re.IGNORECASE)
    definite = re.compile(rf"\s*{escaped}\s*#?\s*(\d+)\s*\/\s*(\d+)\s*", re.IGNORECASE)
    for title in submissions():
        defmatch = re.search(definite, title)
        if defmatch:
            return f"[{name} #{int(defmatch.group(1)) + 1}/{defmatch.group(2)}]"
        indefmatch = re.search(indefinite, title)
        if indefmatch:
            return f"[{name} #{int(indefmatch.group(1)) + 1}]"
    return f"[{name} #1]"


def _submitImage(title, path):
    """upload an image post, supports praw 7 (submit_image) and praw 8+ (submit(image=...))"""
    started = time.time()
    try:
        if hasattr(pg, "submit_image"):
            submission = pg.submit_image(title=title, image_path=path)
        else:
            from praw.models import PostMedia  # pylint: disable=import-outside-toplevel

            submission = pg.submit(title=title, image=PostMedia(path))
        if submission:
            return submission
    except WebSocketException as e:
        # the post is usually created even when reddit's websocket fails
        colormsg(
            f"Reddit had trouble confirming the image upload ({e}), looking for the post",
            fg.yellow,
        )
    for _ in range(10):
        submission = latestSubmission()
        if submission and submission.created_utc >= started - 60:
            return submission
        time.sleep(3)
    raise RuntimeError(
        f"Could not find the uploaded round, check https://reddit.com/r/{pg.display_name}/new"
    )


def submitRound(r):
    title = " ".join(
        part
        for part in (
            getRoundPrefix(),
            getSeriesPrefix(r.get("series")),
            str(r["title"]).strip(),
        )
        if part
    )
    if r.get("path"):
        path = resolveImagePath(r["path"])
        colormsg(f"Uploading {path}...", fg.cyan)
        submission = _submitImage(title, path)
    else:
        submission = pg.submit(title=title, url=str(r["url"]).strip())

    message = r.get("message")
    if message:
        time.sleep(MESSAGE_DELAY)
        if safeReply(submission, str(message)):
            colormsg(f"Message posted to thread: {message}")

    return submission
