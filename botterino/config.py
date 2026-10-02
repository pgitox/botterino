import os
import random
import socket
import sys
import webbrowser
from urllib.parse import parse_qs, urlparse

import praw
from sty import fg

from . import botfiles, settings
from .Utils.color import colormsg

REDIRECT_URI = "http://localhost:8080"
SCOPES = ["identity", "history", "read", "edit", "submit", "privatemessages"]


def receive_connection():
    """
    Wait for and then return a connected socket..
    Opens a TCP connection on port 8080, and waits for a single client.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    return client


def send_message(client, message):
    """
    Send message to client and close the connection.
    """
    client.send(
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{}".format(
            message
        ).encode("utf-8")
    )
    client.close()


def fail(message, error=None):
    colormsg(message, fg.red)
    if error:
        colormsg(f"{type(error).__name__}: {error}", fg.red)
    sys.exit(1)


def browserLogin():
    """log in with OAuth through the browser, for accounts with 2fa"""
    reddit = praw.Reddit("botterino", redirect_uri=REDIRECT_URI)
    state = str(random.randint(0, 65000))
    url = reddit.auth.url(scopes=SCOPES, state=state, duration="permanent")
    colormsg(
        f"A window will be opened in the browser to complete the login process to reddit. If it does not open, visit {url}"
    )
    webbrowser.open(url)

    client = receive_connection()
    data = client.recv(1024).decode("utf-8")
    params = {
        k: v[0] for k, v in parse_qs(urlparse(data.split(" ", 2)[1]).query).items()
    }

    if state != params.get("state"):
        send_message(client, "State mismatch, please try again.")
        fail("Login failed: state mismatch, please try again.")
    if "error" in params or "code" not in params:
        send_message(client, f"Login failed: {params.get('error', 'no code')}")
        fail(f"Login failed: {params.get('error', 'no code received')}")

    refresh_token = reddit.auth.authorize(params["code"])
    send_message(
        client, "Logged in! You can close this window and return to botterino."
    )
    colormsg(
        f"Add this line to the [botterino] section of {botfiles.prawconfig} so you don't have to log in again:",
        fg.blue,
    )
    colormsg(f"refresh_token={refresh_token}", fg.blue)
    return reddit


def login():
    cwd = os.getcwd()
    try:
        # praw looks for praw.ini in the current directory
        os.chdir(botfiles.botconfig)
        reddit = praw.Reddit("botterino")
        me = reddit.user.me()
        if not me:
            colormsg(
                f"No username/password or refresh_token found in {botfiles.prawconfig}, logging in through the browser instead",
                fg.yellow,
            )
            reddit = browserLogin()
            me = reddit.user.me()
        if not me:
            fail(f"Unable to login to reddit. Please check {botfiles.prawconfig}")
    except Exception as e:  # pylint: disable=broad-except
        fail(
            f"Unable to login to reddit. Please check {botfiles.prawconfig}, see the README for help",
            e,
        )
    finally:
        os.chdir(cwd)
    colormsg(f"Successfully logged into reddit as {me}", fg.green)
    return reddit, str(me)


reddit, username = login()

subredditName = settings.get("subreddit", "picturegame").strip() or "picturegame"
debug = subredditName.lower() != "picturegame"
pg = reddit.subreddit(subredditName)

donotreply = {
    "achievements-bot",
    username.lower(),
    "r-picturegame",
    "imreallycuriousbird",
} | {
    u.strip().lower() for u in settings.get("ignore_users", "").split(",") if u.strip()
}

api = "https://api.picturega.me"
