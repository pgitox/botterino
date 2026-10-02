import json
import os
import sys
from configparser import ConfigParser
from pathlib import Path

from . import configure


class Files:
    def __init__(self, botconfig):
        self.home = os.path.expanduser("~")
        self.botconfig = botconfig
        self.configfile = os.path.join(self.botconfig, "config.ini")
        self.roundsdir = os.path.join(self.botconfig, "rounds")
        self.rounds = os.path.join(self.roundsdir, "rounds.yaml")
        self.archive = os.path.join(self.roundsdir, "archive.yaml")
        self.prawconfig = os.path.join(self.botconfig, "praw.ini")
        self.hintfile = os.path.join(self.botconfig, "hints.yaml")
        self.mapsdir = os.path.join(self.botconfig, "maps")
        self.imagesdir = os.path.join(self.botconfig, "images")


PRAW_TEMPLATE = """\
; fill in the values after the equals signs, see the README for details

; Option 1: username/password (use this if your account does NOT have 2fa)
[botterino]
client_id=
client_secret=
username=
password=
user_agent=botterino for /r/picturegame by /u/<your username>

; Option 2: OAuth (use this if your account has 2fa)
; leave username/password out, run the bot once and log in through the browser,
; then paste the refresh_token it prints here
; [botterino]
; client_id=
; client_secret=
; refresh_token=
; user_agent=botterino for /r/picturegame by /u/<your username>
"""

# every option in config.ini with its default value
# missing options are added to an existing config.ini so new settings are discoverable
DEFAULTS = {
    "correct_message": "+correct",
    "incorrect_message": "❌",
    # folder searched first for relative image paths in rounds.yaml, empty means botterino-config/images
    "images_dir": "",
    # open the map of guesses in a browser when a round ends
    "open_map": "true",
    # save a map of guesses to botterino-config/maps
    "save_map": "true",
    # colored output: auto, always or never (the NO_COLOR environment variable also disables it)
    "color": "auto",
    # clickable links in the terminal: auto, always or never
    "hyperlinks": "auto",
    # subreddit to post rounds to, only change this for testing
    "subreddit": "picturegame",
    # extra usernames to never reply to, comma separated
    "ignore_users": "",
    # unused, kept for compatibility with older config files
    "hints": "[25,45]",
}


def prepare(directory):
    """creates any missing files in the config directory and returns its Files and settings"""
    files = Files(directory)
    for d in [files.botconfig, files.roundsdir]:
        Path(d).mkdir(parents=True, exist_ok=True)
    for f in [files.rounds, files.archive, files.hintfile]:
        with open(f, "a+", encoding="utf-8"):
            pass
    if not os.path.exists(files.prawconfig) or not os.path.getsize(files.prawconfig):
        with open(files.prawconfig, "w", encoding="utf-8") as f:
            f.write(PRAW_TEMPLATE)

    configParser = ConfigParser(interpolation=None)
    configParser.read(files.configfile, encoding="utf-8")
    if not configParser.has_section("config"):
        configParser.add_section("config")
    missing = [k for k in DEFAULTS if not configParser.has_option("config", k)]
    for k in missing:
        configParser.set("config", k, DEFAULTS[k])
    if missing:
        try:
            with open(files.configfile, "w", encoding="utf-8") as f:
                configParser.write(f)
        except OSError:
            pass

    images = configParser["config"]["images_dir"].strip()
    if images:
        files.imagesdir = configure.normalize(images)
    Path(files.imagesdir).mkdir(parents=True, exist_ok=True)
    return files, configParser["config"]


setupRan = False
if configure.isFirstRun() and sys.stdin.isatty() and sys.stdout.isatty():
    configure.runSetup(firstRun=True)
    setupRan = True

botfiles, settings = prepare(configure.configDir())


def getBool(option):
    try:
        return settings.getboolean(option)
    except ValueError:
        return DEFAULTS[option].lower() == "true"


correctMessage = settings["correct_message"]
incorrectMessage = settings["incorrect_message"]
try:
    hints = json.loads(settings["hints"])
except ValueError:
    hints = []
