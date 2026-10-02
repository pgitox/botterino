import functools
from time import sleep

from praw.exceptions import RedditAPIException
from prawcore.exceptions import (
    BadRequest,
    RequestException,
    ResponseException,
    ServerError,
)
from requests.exceptions import ConnectionError, Timeout
from sty import fg

from ..Utils.color import colormsg

RETRY_SECONDS = 10


def _log(message):
    colormsg(message, fg.yellow)


def retry(action):
    """
    Perform the given action. If a network or reddit error is raised, retry every ten seconds
    Returns the return value of the action, or None on a 400 Bad Request
    """

    @functools.wraps(action)
    def actionWithRetry(*args, **kwargs):
        failCount = 0

        while True:
            try:
                result = action(*args, **kwargs)
                if failCount:
                    _log(
                        f"Reddit is reachable again after {failCount} failed attempt(s)"
                    )
                return result

            except BadRequest:
                # Don't keep trying if we get a bad request
                # This is likely caused by deleted accounts so we can safely ignore them
                return None

            except RedditAPIException as e:
                failCount += 1
                if failCount == 1:
                    _log(
                        f"Reddit returned an error, retrying every {RETRY_SECONDS}s: {e}"
                    )
                sleep(RETRY_SECONDS)

            except (
                ConnectionError,
                Timeout,
                ResponseException,
                RequestException,
                ServerError,
            ) as e:
                failCount += 1
                if failCount == 1:
                    _log(
                        f"Could not reach reddit, retrying every {RETRY_SECONDS}s: {type(e).__name__} {e}"
                    )
                sleep(RETRY_SECONDS)

    return actionWithRetry
