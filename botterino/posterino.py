import requests
import time
import json
from RedditPoller.Retry import retry
from botterino.hosterino import check
from config import *

def post_delay():
    if debug:
        return -1

    r = requests.get('https://api.picturegame.co/current')
    data = json.loads(r.content)
    tries = 1

    while data['round']['hostName'].lower() != username.lower():
        tries += 1
        if tries > 5:
            return -1
        r = requests.get('https://api.picturegame.co/current')
        data = json.loads(r.content)
        time.sleep(5)

    return data['round'].get('postDelay', -1)

def post_round(r):
    submission = pg.submit(title=f'{round_prefix()} {r["title"]}',
                           url=r['url'].strip())

    print(f'round \'{r["title"]}\' posted in {post_delay()}s')

    message = r.get('message')
    after = r.get('after')
    if message is not None:
        time.sleep(15)
        submission.reply(message)

    if 'tolerance' in r:
        print('checking answers on round...')
        answer = r['answer']
        tolerance = float(r['tolerance'])
        manual = r.get('manual', False)
        check(submission, answer, tolerance, manual)
    elif 'tolerances' in r:
        answer = r['answers']
        tolerance = [float(t) for t in r['tolerances']]
        if len(answer) != len(tolerance):
            print('Refusing to check answers, number of tolerances must equal number of answers.') 
        manual = r.get('manual', False)
        check(submission, answer, tolerance, manual, multiple=True)

    while approved_to_host():
        continue
    if after:
        submission.reply(after)

def round_prefix():
    r = requests.get('https://api.picturegame.co/current')
    roundnum = int(json.loads(r.content)['round']['roundNumber']) + 1
    return f'[Round {roundnum}]'


def approved_to_host():
    c = next(iter(pg.contributor()))
    return c and c.name.lower() == username.lower()

@retry
def wait():
    while not approved_to_host():
        continue
    print('Round was posted')
