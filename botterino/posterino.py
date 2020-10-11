import os
import yaml
import requests
import time
import json
from botterino.hosterino import check
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

def post_delay():
    if debug:
        return -1

    r = requests.get('https://api.picturegame.co/current')
    data = json.loads(r.content)

    while data['round']['hostName'].lower() != username.lower():
        r = requests.get('https://api.picturegame.co/current')
        data = json.loads(r.content)
        time.sleep(5)

    return data['round']['postDelay']

def post_round(r):
    submission = pg.submit(title=f'{round_prefix()} {r["title"]}',
                           url=r['url'].strip())
    
    print(f'round \'{r["title"]}\' posted in {post_delay()}s')
    
    message = r.get('message')
    if message is not None:
        time.sleep(15)
        submission.reply(message)
    time.sleep(0 if message is not None else 5)

    if 'tolerance' in r:
        print('checking answers on round...')
        answer = r['answer']
        tolerance = float(r['tolerance'])
        manual = r.get('manual', False)
        check(submission, answer, tolerance, manual)
    while approved_to_host():
        continue


def round_prefix():
    r = requests.get('https://api.picturegame.co/current')
    roundnum = int(json.loads(r.content)['round']['roundNumber']) + 1
    return f'[Round {roundnum}]'


def approved_to_host():
    if debug:
        return 

    c = next(iter(pg.contributor()))
    return c and c.name.lower() == username.lower()


def wait():
    if not debug:
        while not approved_to_host():
            continue
