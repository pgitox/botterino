"""
Host a round that is already live, e.g. after posting manually or a crash.
Run with `python -m botterino.failure`
"""

import traceback

from sty import fg

from .botterino import hostRound, nextValidRound
from .config import username
from .hosterino import checkAnswer, reportResult, roundFields
from .Utils.color import colormsg
from .Utils.utils import (
    getCurrentComments,
    hasHostReplied,
    isCorrection,
    latestSubmission,
)


def processUnrepliedComments(submission, r):
    """
    replies to guesses made while botterino was not running
    returns (corrected, ids of the comments that were looked at)
    """
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
    comments = getCurrentComments(submission) or []
    if any(c.author and isCorrection(c, submission) for c in comments):
        colormsg("This round has already been corrected", fg.yellow)
        return True, set()
    comments.sort(key=lambda c: c.created_utc)
    seen = {c.id for c in comments}
    for c in comments:
        if (
            not c.is_root
            or not c.author
            or c.author.name.lower() in ["r-picturegame", username.lower()]
            or hasHostReplied(c)
        ):
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
                None,
            )
            if reportResult(c, result, manual):
                return True, seen
        except Exception:  # pylint: disable=broad-except
            colormsg(f"Error checking https://reddit.com{c.permalink}:", fg.red)
            colormsg(traceback.format_exc(), fg.red)
    return False, seen


def main():
    k, r = nextValidRound()

    submission = latestSubmission()
    if not submission:
        colormsg(f"Could not find a round posted by {username}", fg.red)
        return
    colormsg(
        f"Checking answers on https://reddit.com{submission.permalink}",
    )

    corrected, seen = processUnrepliedComments(submission, r)
    if corrected:
        return
    hostRound(k, r, submission, skip=seen)


if __name__ == "__main__":
    main()
