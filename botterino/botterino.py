import os
import time
import traceback
from importlib.metadata import version
from threading import Event, Thread

import ruamel.yaml
from sty import fg

from .config import username
from .hosterino import checkAnswers, checkHints
from .Loader.loader import getRound, hintfile, peekRound, roundfile
from .posterino import submitRound
from .Utils.color import colormsg
from .Utils.utils import (
    latestSubmission,
    postDelay,
    safeReply,
    waitForApproval,
    waitWhileApproved,
)
from .validate import checkFiles, roundErrors

RETRY_SECONDS = 10


def checkForUpdates():
    try:
        from update_checker import (
            UpdateChecker,
        )  # pylint: disable=import-outside-toplevel

        result = UpdateChecker().check("botterino", version("botterino"))
    except Exception:  # pylint: disable=broad-except
        return
    if result:
        colormsg(result, fg.yellow)
        colormsg('run "pip install --upgrade botterino" to update', fg.yellow)


def checkType(r):
    types = []
    if "tolerance" in r and "answer" in r:
        types.append("coordinates")
    if "tolerances" in r and "answers" in r:
        types.append("multiple coordinates")
    if "text" in r and "similarity" in r:
        types.append("text match")
    if r.get("manual"):
        types.append("x wrong guesses with manual correct")
    if not types:
        return "no automatic replies"
    if not r.get("manual"):
        types.append("automatic")
    return ", ".join(types)


class FileWatcher:
    """re-validates the round and hint files whenever they change"""

    def __init__(self, *files):
        self.files = files
        self.mtimes = self._mtimes()

    def _mtimes(self):
        return [os.path.getmtime(f) if os.path.exists(f) else None for f in self.files]

    def __call__(self, spinner=None):
        mtimes = self._mtimes()
        if mtimes == self.mtimes:
            return
        self.mtimes = mtimes
        if spinner:
            spinner.stop()
        colormsg("Round files changed, checking them again...", fg.cyan)
        checkFiles()
        if spinner:
            spinner.start()


def nextValidRound(stop=None):
    """
    waits until the top round in rounds.yaml exists and has no errors,
    then removes it from rounds.yaml and returns (key, round)
    """
    lastProblem = None
    while not stop:
        problem = None
        try:
            top = peekRound()
            if not top:
                problem = f"No rounds in {roundfile}! Add one, checking again every {RETRY_SECONDS}s"
            else:
                errors = roundErrors(top[1])
                if errors:
                    problem = (
                        f"Round '{top[0]}' can't be posted until it is fixed in {roundfile}: "
                        + "; ".join(errors)
                    )
        except ruamel.yaml.YAMLError as e:
            problem = f"{roundfile} is not valid yaml, fix it to post your round:\n{e}"
        if not problem:
            return getRound()
        if problem != lastProblem:
            colormsg(problem, fg.red)
            lastProblem = problem
        time.sleep(RETRY_SECONDS)
    return None


def postRound(r, attempts=5):
    """submits the round, retrying on errors without posting it twice"""
    started = time.time()
    for attempt in range(attempts):
        try:
            return submitRound(r)
        except Exception:  # pylint: disable=broad-except
            colormsg(f"Failed to post your round:\n{traceback.format_exc()}", fg.red)
            if attempt == attempts - 1:
                raise
        latest = latestSubmission()
        if latest and latest.created_utc >= started - 60:
            colormsg("Looks like your round was posted anyway", fg.yellow)
            return latest
        colormsg(f"Trying again in {RETRY_SECONDS}s...", fg.yellow)
        time.sleep(RETRY_SECONDS)
    return None


def hostRound(k, r, submission, stop=None, skip=()):
    """checks answers and posts hints until the round is over"""
    colormsg(f"Checking Answers: {checkType(r)}...", fg.cyan)

    # Create an event to signal that the round is over
    round_over = Event()

    CheckAnswers = Thread(
        target=checkAnswers, args=(r, submission, k, skip), daemon=True
    )
    CheckHints = Thread(
        target=checkHints, args=(k, submission, round_over), daemon=True
    )
    CheckAnswers.start()
    CheckHints.start()

    # Wait for threads to finish
    CheckAnswers.join()
    round_over.set()
    CheckHints.join()

    colormsg("Round over! Waiting for the next round to start...", fg.cyan)
    waitWhileApproved(stop)
    after = r.get("after")
    if after and safeReply(submission, str(after)):
        colormsg(f"Posted your message after the round: {after}")


def main(stop=None):
    checkForUpdates()
    checkFiles()
    watcher = FileWatcher(roundfile, hintfile)
    while True:
        colormsg(f"Waiting for {username} to win a round... 🐌", fg.yellow)
        stopped = waitForApproval(stop, onTick=watcher)
        if stopped or stop:
            colormsg("Stopped botterino", fg.red)
            return
        colormsg(f"Congrats on a well deserved win {username}! ⭐", fg.blue)
        nextRound = nextValidRound(stop)
        if not nextRound:
            colormsg("Stopped botterino", fg.red)
            return
        k, r = nextRound
        submission = postRound(r)
        colormsg(
            f"Your round was posted to https://reddit.com{submission.permalink}",
            fg.green,
        )
        colormsg(f"Round '{r['title']}' posted in {postDelay()}s", fg.magenta)
        hostRound(k, r, submission, stop)


if __name__ == "__main__":
    main()
