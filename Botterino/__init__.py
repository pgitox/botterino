import os
from pathlib import Path

class files():
    def __init__(self):
        self.home = os.path.expanduser('~')
        self.botconfig = os.path.join(self.home, 'botterino-config')
        self.roundsdir = os.path.join(self.botconfig, 'rounds')
        self.rounds = os.path.join(self.roundsdir, 'rounds.yaml')
        self.archive = os.path.join(self.roundsdir, 'archive.yaml')
        self.prawconfig = os.path.join(self.botconfig, 'praw.ini')

botfiles = files()
dirs = [botfiles.botconfig, botfiles.roundsdir]
files = [botfiles.rounds, botfiles.archive, botfiles.prawconfig]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
for f in files:
    with open(f, 'a+'):
        pass
