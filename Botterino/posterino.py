from .config import pg
from .Utils.utils import randomColor, getRoundPrefix
from sty import fg
import time

def submitRound(r):
    submission = pg.submit(title=f'{getRoundPrefix()} {r["title"]}',
                           url=r['url'].strip())

    message = r.get('message')
    if message is not None:
        time.sleep(15)
        submission.reply(message)

        print(f'{randomColor()}Message posted to thread: {message}', end=f'{fg.rs}\n')

    return submission