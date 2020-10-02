import os
import yaml
import requests
import time
import json
from hosterino import check
from config import *


def load_rounds():
    with open(roundfile, 'r') as rounds:
        x = yaml.load(rounds)
    if not x:
        return
    clear_rounds()
    return [x[key] for key in x]


def clear_rounds():
    with open(archivefile, 'a') as archive, open(roundfile, 'r') as old:
        archive.write(''.join(old.readlines()))
        archive.write('\n')
    os.remove(roundfile)
    with open(roundfile, 'w') as f:
        f.write('')


def post_round(r):
    submission = pg.submit(title=f'{round_prefix()} {r["title"]}',
                           url=r['url'].strip())
    message = r.get('message')
    if 'tolerance' not in r and message is not None:
        time.sleep(15)
        submission.reply(message)
    print(f'round {r} has been posted')
    if 'tolerance' in r:
        time.sleep(15)
        submission.reply(clarification)
        if message is not None:
            submission.reply(message)
        print('checking answers on round...')
        answer = r['answer']
        tolerance = float(r['tolerance'])
        check(submission, answer, tolerance)
    while approved_to_host():
        continue


def round_prefix():
    r = requests.get('https://api.picturegame.co/current')
    roundnum = int(json.loads(r.content)['round']['roundNumber']) + 1
    return f'[Round {roundnum}]'


def approved_to_host():
    c = next(iter(pg.contributor()))
    return c and c.name.lower() == username.lower()


def wait():
    while not approved_to_host():
        continue
