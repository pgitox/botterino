# Botterino

Botterino automates hosting and posting of /r/picturegame coordinate rounds.

- 🏁 **Win a round, and your next round is posted automatically** as soon as you are approved to host
- ✅ **Replies `+correct` or `❌` to guesses** with configurable distance tolerances, multiple coordinates or text matching
- 🖼️ **Post image links or upload images straight from your computer**
- 💡 **Scheduled hints**, messages when a round starts or ends, and automatic series numbering
- 🗺️ **A live map of everyone's guesses** saved for every round
- 🔍 **Checks your round files for mistakes** before you win, not after

---

## Install

1. Install [Python](https://www.python.org/downloads/) 3.8 or newer
    1. on windows it is easiest to install python from the [microsoft store](https://apps.microsoft.com/search?query=python)
2. Open a terminal (or command prompt) and run `pip install botterino`
3. Run `python -m botterino`. The first time, a short setup asks where botterino should keep its files
   and where your round images are. Press enter to accept the defaults.
   You can run the setup again any time with `python -m botterino.configure`

All the files you interact with live in the **botterino-config** folder. By default that is:

| OS      | Location                               |
|---------|----------------------------------------|
| windows | `C:\Users\<your username>\botterino-config` |
| mac     | `/Users/<your username>/botterino-config` |
| linux   | `~/botterino-config`                   |

To keep it somewhere else, choose a different folder in the setup or set the `BOTTERINO_CONFIG` environment variable.

```
botterino-config/
├── praw.ini          reddit login
├── config.ini        settings
├── hints.yaml        scheduled hints
├── images/           images for 'path:' rounds (configurable)
├── maps/             maps of guesses for each round
└── rounds/
    ├── rounds.yaml   rounds waiting to be posted
    └── archive.yaml  rounds that have been posted
```

### Reddit login

[Create a Reddit app](https://www.reddit.com/prefs/apps/) and add its details to `botterino-config/praw.ini`
(see [`sample-praw.ini`](sample-praw.ini)):

1. Give the app any name, such as 'botterino'
2. Choose 'script' as the app type
3. Fill in 'redirect URI' with `http://localhost:8080`
4. Once created, copy the 'secret' into `client_secret`
5. Copy the client id (under the app name and the words 'personal use script') into `client_id`
6. Fill in your Reddit `username`, `password` and anything you like for `user_agent`

**Accounts with 2fa:** leave out `username` and `password`. When you run botterino, log in through the browser
window that opens, then paste the `refresh_token` it prints into `praw.ini` so you don't have to log in again.

---

## Usage

1. Add rounds to `botterino-config/rounds/rounds.yaml`.
   See [`sample-rounds.yaml`](sample-rounds.yaml) for every kind of round botterino supports.
2. Run `python -m botterino`
3. Win! Until you win, botterino just waits. When you are approved to host, the top round in `rounds.yaml` is posted.

```yaml
vegas_round:
  title: 'What are my coordinates?'
  url: https://i.imgur.com/qBRRrbD.jpg
  answer: 36.170439, -115.139889
  tolerance: 50
```

Rounds added to `rounds.yaml` while botterino is running are picked up automatically, no need to restart.
Once a round is posted it moves to `rounds/archive.yaml`.

### Uploading images

Use `path` instead of `url` to upload an image from your computer:

```yaml
upload_round:
  title: 'What are my coordinates?'
  path: vegas.jpg
  answer: 36.170439, -115.139889
  tolerance: 50
```

Relative paths are looked up in your images folder first (`botterino-config/images` unless you picked another
folder in the setup), then in `botterino-config/rounds`, then in the folder you started botterino from.
Absolute paths work too; on windows write them in single quotes (`'C:\Users\me\Pictures\vegas.jpg'`) or with forward
slashes. png, jpg and gif images up to 20MB are supported.

### Checking your rounds

Botterino checks `rounds.yaml` and `hints.yaml` when it starts and every time you save them while it is waiting,
and warns you about problems like invalid yaml, missing titles, bad coordinates, images that don't exist,
typos in field names and rounds with duplicate names. If the next round has an error when you win, botterino waits
for you to fix it instead of posting something broken.

You can also check them yourself at any time:

```
python -m botterino.validate
```

### Hints

Botterino can post hints on a schedule. Entries in `botterino-config/hints.yaml` are matched to rounds by name.
See [`sample-hints.yaml`](sample-hints.yaml) for the syntax. `hints.yaml` can be edited while a round is running.

### Map of guesses

For coordinate rounds, every guess is plotted on a map with the answer and its tolerance, saved to
`botterino-config/maps`. The map is updated after every guess, so you can refresh it in your browser during the round.
When the round ends it opens in your browser, set `open_map = false` in `config.ini` to turn that off.

### Live rounds

Botterino can take over a round that is already live, for example if you posted manually or botterino crashed while hosting.

1. Make sure the round is at the top of `rounds.yaml`
2. Run `python -m botterino.failure`

Botterino replies to the guesses it missed, then continues hosting as usual.

### UI

`python -m botterino.ui` opens a small window to add rounds to `rounds.yaml` (including picking an image to upload)
and to start and stop the bot.

---

## Settings

Settings live in `botterino-config/config.ini`. New settings are added automatically with their defaults when you update.

| Setting             | Default        | Description |
|---------------------|----------------|-------------|
| `correct_message`   | `+correct`     | reply to correct guesses |
| `incorrect_message` | `❌`           | reply to incorrect guesses |
| `images_dir`        | *(empty)*      | folder searched first for image `path`s, empty means `botterino-config/images` |
| `open_map`          | `true`         | open the map of guesses in your browser when a round ends |
| `save_map`          | `true`         | save a map of guesses for coordinate rounds |
| `color`             | `auto`         | colored output: `auto`, `always` or `never`. The `NO_COLOR` environment variable also turns it off |
| `hyperlinks`        | `auto`         | clickable links in the terminal: `auto`, `always` or `never` |
| `ignore_users`      | *(empty)*      | comma separated usernames botterino never replies to |
| `subreddit`         | `picturegame`  | only change this for testing |

---

## Commands

| Command                           | What it does |
|-----------------------------------|--------------|
| `python -m botterino`             | run the bot |
| `python -m botterino.validate`    | check `rounds.yaml` and `hints.yaml` for mistakes |
| `python -m botterino.configure`   | run the setup again (config folder, images folder, map) |
| `python -m botterino.failure`     | take over a round that is already live |
| `python -m botterino.ui`          | open the UI |

The same commands are also installed as `botterino`, `botterino-check`, `botterino-setup`, `botterino-failure` and `botterino-ui`.

## Update

```
pip install --upgrade botterino
```

## Troubleshooting

* **Bot does not run, crash message shows a 403 error, everything in praw.ini looks correct**: try a different `user_agent`
* **`praw.ini` errors about a duplicate section**: only one `[botterino]` section may be uncommented
* **Strange characters instead of colors on windows**: botterino turns on color support in the windows console
  automatically. If you still see codes like `[38;5;...m`, use [Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701)
  or set `color = never` in `config.ini`
