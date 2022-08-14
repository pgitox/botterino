import math
from .config import pg
from .Utils.utils import randomColor, getRoundPrefix, submissions
from sty import fg
import time
import re

def getSeriesPrefix(name):
    if not name:
        return ''
    name = name.strip()
    indefinite = re.compile(f'\s*{name}\s*#?\s*(\d+)\s*')
    definite = re.compile(f'\s*{name}\s*#?\s*(\d+)\s*\/\s*(\d+)\s*')
    for title in submissions():
        defmatch = re.search(definite, title)
        if defmatch:
            return f'[{name} #{int(defmatch.group(1)) + 1}/{defmatch.group(2)}]'
        indefmatch = re.search(indefinite, title)
        if indefmatch:
            return f'[{name} #{int(indefmatch.group(1)) + 1}]'
    return f'[{name} #1]'

def submitRound(r):
    series_prefix = getSeriesPrefix(r.get('series'))
    title = f'{getRoundPrefix()} {series_prefix} {r["title"]}'
    submission = pg.submit(title=title,
                           url=r['url'].strip())

    message = r.get('message')
    if message is not None:
        time.sleep(15)
        submission.reply(message)

        print(f'{randomColor()}Message posted to thread: {message}', end=f'{fg.rs}\n')

    return submission