from sty import fg
import requests 
import os 
import tempfile

baseURL = 'https://raw.githubusercontent.com/pgitox/botterino/master/{}'

files = [
    'Botterino/hosterino.py',
    'Botterino/posterino.py',
    'Loader/loader.py',
    'RedditPoller/RedditPoller.py',
    'RedditPoller/Retry.py',
    'Rounds/sample.yaml',
    'Utils/utils.py',
    'Utils/update.py',
    '.gitignore',
    'botterino.py',
    'config.py',
    'failure.py',
    'README',
    'requirements.txt'
]

def updateFile(f, content):
    with open(f, 'w') as new:
        new.write(content)
    print(f'{fg.green}Sucessfully updated file {f}')

def hasUpdate():
    for f in files:
        r = requests.get(baseURL.format(f))
        with open(f, 'r') as old:
            if r.content != old.read():
                return True
    return False

def doUpdate(): 
    for f in files:
        r = requests.get(baseURL.format(f))
        with open(f, 'r') as old:
            if r.content != old.read():
                updateFile(f, r.content)