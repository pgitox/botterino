from .utils import randomColor
import requests
import os.path

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
    'README.md',
    'requirements.txt'
]


def updateFile(f):
    r = requests.get(baseURL.format(f))
    content = r.text.strip().replace('\r\n', '\n')
    with open(f, 'w', encoding='utf-8') as new:
        new.write(content)
    print(f'{randomColor()}Successfully updated file {f}')


def fileHasUpdate(f):
    r = requests.get(baseURL.format(f))
    if not os.path.isfile(f):
        return True
    with open(f, 'r', encoding='utf=8') as old:
        old = old.read().strip().replace('\r\n', '\n')
        new = r.text.strip().replace('\r\n', '\n')
        if old != new:
            return True
    return False


def hasUpdate():
    for f in files:
        if fileHasUpdate(f):
            return True
    return False


def doUpdate():
    for f in files:
        if fileHasUpdate(f):
            updateFile(f)
