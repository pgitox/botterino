# Botterino

Botterino allows automation of hosting and posting of /r/picturegame coordinates rounds

When running botterino, if you win a round, your round will automatically be posted.
It will reply with 'x' or '+correct' to any comments on your round automatically, with configurable tolerances.

---

## Pre-requisites

0. All the files you interact with will live in the botterino-config folder which is located:
    1. windows: `C:\Users\your username\botterino-config`
    2. mac: `/Users/<your username/botterino-config`
    3. linux: `~/botterino-config`
    These files are created for you the first time you run the bot
1. You must have [Python](https://www.python.org/downloads/) installed on your computer
    1. If on windows it is best to install python from the [microsoft store](https://www.microsoft.com/en-us/p/python-39/9p7qfqmjrfp7?activetab=pivot:overviewtab)
2. Install the bot
    1. open a terminal or command prompt window and type the following command: `pip install botterino`
3. You must [create a Reddit app](https://www.reddit.com/prefs/apps/) and add authentication details in
    `botterino-config/praw.ini`; see `sample-praw.ini` (on github) for an example
    1. Give app any name you choose, such as 'botterino'
    2. Choose 'script' as app type
    3. Fill in 'redirect URI' with `http://localhost:8080` (This is irrelevant unless OAuth2 is used,but it's a required field)
    4. Once created, you'll have a 'secret', copy/paste that as `client_secret` in botterino-config/praw.ini
    5. You'll also have a less obvious client id, in the top left under the app name and the words 'personal use script' - copy/paste that into `client_id` in praw.ini
4. Fill out the rest of 'botterino-config/praw.ini' with your Reddit username/password as well as anything you want for `user_agent`

---

## Usage

- add round(s) in botterino-config/rounds/rounds.yaml. See sample-rounds.yaml on botterino github page for information on round syntax and types of features supported.
- run with `python -m botterino`

## UI:
- The ui can be launched with `python -m botterino.ui`
- Through the ui you can automatically populate rounds.yaml and start/stop the bot

### Normal hosting

Rounds are kept in the 'rounds/rounds.yaml' file, see 'sample.yaml' for some examples

#### Steps
1. Add round(s) to 'botterino-config/rounds/rounds.yaml'
2. Open a terminal or command prompt and type `python -m botterino`
    1. Then all you have to do is win. Until you win, botterino will do nothing
    2. When you win, the top round in rounds.yaml is posted as soon as you are approved to host

Any new rounds added to 'botterino-config/rounds/rounds.yaml' while the app is running will automatically be added to the queue, no need to restart.
Once a round is complete, it will be moved to 'botterino-config/rounds/archive.yaml'.

### Live rounds

Botterino can be used on a round that is already live

This is useful for cases where
1. You post manually and decide you would like bot to host
2. Bot posts for you but crashes during hosting for some reason

#### Steps
1. Will use the top round in rounds.yaml
    1. `url` field should be omitted
2. Run with `python -m botterino.failure`

### Hints:
Botterino can schedule hints and post them automatically.
The file `botterino-config/hints.yaml` will be scanned for entries with the same key
as the corresponding entry in `botterino-config/rounds.yaml`. See `sample-hints.yaml` for syntax.

---

## Misc

### Customize
Options such as correct message and incorrect message can be customized in botterino-config/config.ini

### Update
Update this botterino with
`pip install --upgrade botterino`

### Issues
* Bot does not run, crash message shows 403 error, everything in praw.ini looks correct
    1. try a different user agent


### Colors on windows
This botterino uses colorful output. If you see strange output like this on windows
![Strange windows output](https://cdn.discordapp.com/attachments/768582651669381191/830607745769930762/unknown.png)
then download [Windows terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701?rtc=1)
from the Microsoft store.

