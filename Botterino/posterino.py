from .config import pg
from .Utils.utils import randomColor, getRoundPrefix
import time

def submitRound(r):
    submission = pg.submit(title=f'{getRoundPrefix()} {r["title"]}',
                           url=r['url'].strip())

    message = r.get('message')
    if message is not None:
        time.sleep(15)
        submission.reply(message)

        print(f'{randomColor()}Message posted to thread: {message}')

    return submission