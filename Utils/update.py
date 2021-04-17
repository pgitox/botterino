from .utils import randomColor
import requests 

baseURL = 'https://raw.githubusercontent.com/pgitox/botterino/master/{}'

files = [
    'Botterino/hosterino.py',
    'Botterino/posterino.py',
    'Loader/loader.py',
    'RedditPoller/RedditPoller.py',
    'RedditPoller/Retry.py',
    'Rounds/sample.yaml',
    'Utils/utils.py',
    'Utils/update.py'
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
    print(f'{randomColor()}Successfully updated file {f}')

def hasUpdate():
    for f in files:
        r = requests.get(baseURL.format(f))
        with open(f, 'r') as old:
            if r.text.strip() != old.read().strip():
                return True
    return False

def doUpdate(): 
    for f in files:
        r = requests.get(baseURL.format(f))
        with open(f, 'r') as old:
            old = old.read().strip()
            new = r.text.strip()
            if old != new:
                updateFile(f, new)