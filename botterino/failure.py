from .hosterino import checkAnswers, checkHints, checkAnswer
from .config import pg, correctMessage, incorrectMessage, username
from .Utils.color import colormsg
from .Utils.utils import approved, getCurrentComments, hasHostReplied
from .Loader import loader
from sty import fg
import time
from threading import Thread, Event
from datetime import datetime


def processUnrepliedComments(submission, r):
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
    comments = getCurrentComments(submission)
    comments.sort(key=lambda c: datetime.fromtimestamp(c.created_utc))
    for c in comments:
        if (
            not hasHostReplied(c)
            and c.author
            and c.author.name.lower() not in ["r-picturegame", username.lower()]
            and c.is_root
        ):
            if checkAnswer(
                c,
                tolerance,
                text,
                answer,
                tolerances,
                answers,
                similarity,
                ignorecase,
                None,
            ):
                colormsg(f"Correct guess found in comment: {c.permalink}", fg.green)
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
            else:
                colormsg(f"Incorrect guess in comment: {c.permalink}", fg.red)
                c.reply(incorrectMessage)


round = loader.getRound()
while not round:
    colormsg(f"No rounds in round file! checking again in 10s", fg.red)
    time.sleep(10)
    round = loader.getRound()
k, r = round

submission = next(iter(pg.new()))
colormsg(
    f"Checking answers on https://reddit.com{submission.permalink}",
)

# Process unreplied comments
processUnrepliedComments(submission, r)

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
