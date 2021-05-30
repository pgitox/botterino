# Botterino

Botterino allows automation of hosting and posting of /r/picturegame coordinates rounds

When running botterino, if you win a round, your round will automatically be posted.
It will reply with 'x' or '+correct' to any comments on your round automatically, with configurable tolerances.

---

## Pre-requisites

1. You must have [Python](https://www.python.org/downloads/) installed on your computer
3. You must install items in 'requirements.txt'
    1. Run the command `pip install -r requirements.txt`
4. You must [create a Reddit app](https://www.reddit.com/prefs/apps/)
    1. Give app any name you choose, such as 'botterino'
    2. Choose 'script' as app type
    3. Fill in 'redirect URI' with `http://localhost:8080` (This is irrelevant but it's a required field)
    4. Once created, you'll have a 'secret', copy/paste that as `client_secret` in praw.ini
    5. You'll also have a less obvious client id, in the top left under the app name and the words 'personal use script' - copy/paste that into `client_id` in praw.ini
5. Fill out the rest of 'praw.ini' with your Reddit username/password as well as anything you want for `user_agent`

---

## Usage

- add round(s) in rounds.yaml
- python botterino.py

### Normal hosting

Rounds are kept in the 'Rounds/rounds.yaml' file, see 'Rounds/sample.yaml' for some examples

#### Steps
1. Add round(s) to 'Rounds/rounds.yaml'
2. Start app with `python botterino.py`

Any new rounds added to 'Rounds/rounds.yaml' while the app is running will automatically be added to the queue, no need to restart.
Once a round is complete, it will be moved to 'Rounds/archive.yaml'.

### Live rounds

Botterino can be used on a round that is already live

This is useful for cases where
1. You post manually and decide you would like bot to host
2. Bot posts for you but crashes during hosting

#### Steps
1. Edit answer and tolerance in 'failure.py'
2. Run with `python failure.py`

---

## Misc

### Disable checking for updates
If the prompt for updating annoys you, add the following line to 'praw.ini'
```donotupdate=true```

### Colors on windows
This botterino uses colorful output. If you see strange output like this on windows
![Strange windows output](https://cdn.discordapp.com/attachments/768582651669381191/830607745769930762/unknown.png)
then download [Windows terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701?rtc=1) from the Microsoft store.

