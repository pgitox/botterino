from .config import pg, username, hints
from .posterino import submitRound
from .hosterino import checkAnswers, checkHints
from .Utils.utils import waitForApproval, approved, postDelay
from .Utils.color import colormsg
from .Loader.loader import getRound
from sty import fg
from importlib.metadata import version
from update_checker import UpdateChecker
from threading import Thread, Event
import time

v = version("botterino")
checker = UpdateChecker()
result = checker.check("botterino", v)
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
    if "manual" in r:
        types.append("x wrong guesses with manual correct")
    if not types:
        return "no automatic replies"
    if "manual" not in r:
        types.append("automatic")
    return ",".join(types)


def main(stop=None):
    while True:
        colormsg(f"Waiting for {username} to win a round... 🐌", fg.yellow)
        stopped = waitForApproval(stop)
        if stopped or stop:
            colormsg("Stopped botterino", fg.red)
            return
        colormsg(f"Congrats on a well deserved win {username}! ⭐", fg.blue)
        k, r = getRound()
        while not r:
            colormsg(f"No rounds in round file! checking again in 10s", fg.red)
            time.sleep(10)
            k, r = getRound()
        submission = submitRound(r)
        colormsg(
            f"Your round was posted to https://reddit.com{submission.permalink}",
        )
        colormsg(f'Round \'{r["title"]}\' posted in {postDelay()}s', fg.magenta)
        colormsg(f"Checking Answers: {checkType(r)}...", fg.cyan)

        # Create an event to signal the round status
        round_active_event = Event()
        round_active_event.set()

        CheckAnswers = Thread(target=checkAnswers, args=(r, submission))
        CheckHints = Thread(target=checkHints, args=(k, submission, round_active_event))
        CheckAnswers.start()
        CheckHints.start()

        # Wait for threads to finish
        CheckAnswers.join()
        round_active_event.clear()  # Clear the event to signal that the round is over
        CheckHints.join()

        while approved():
            continue
        after = r.get("after")
        if after:
            submission.reply(after)
            colormsg(f"Posted your message after the round: {after}")
