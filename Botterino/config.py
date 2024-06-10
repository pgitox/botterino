import praw
import os
import sys
from .Utils.color import colormsg
from . import botfiles, correctMessage, incorrectMessage, hints
from sty import fg
import random
import webbrowser
import socket


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
    client.send("HTTP/1.1 200 OK\r\n\r\n{}".format(message).encode("utf-8"))
    client.close()


if sys.platform == "win32":
    os.system("color")

debug = False
roundfile = botfiles.rounds
archivefile = botfiles.archive
hintfile = botfiles.hintfile
cwd = os.getcwd()
# FIXME: clean this up
try:
    os.chdir(botfiles.botconfig)
    reddit = praw.Reddit("botterino")
    if reddit.user.me():
        colormsg(f"Successfully logged into reddit as {reddit.user.me()}", fg.green)
    else:
        colormsg(
            f"Unable to login with username/password. If your account has 2fa continue in browser. Otherwise check {botfiles.prawconfig}",
            fg.yellow,
        )
        os.chdir(botfiles.botconfig)
        reddit = praw.Reddit("botterino", redirect_uri="http://localhost:8080")
        state = str(random.randint(0, 65000))
        scopes = ["identity", "history", "read", "edit", "submit", "privatemessages"]
        url = reddit.auth.url(scopes, state, "permanent")
        colormsg(
            "A window will be opened in the browser to complete the login process to reddit."
        )
        webbrowser.open(url)

        client = receive_connection()
        data = client.recv(1024).decode("utf-8")
        param_tokens = data.split(" ", 2)[1].split("?", 1)[1].split("&")
        params = {
            key: value for (key, value) in [token.split("=") for token in param_tokens]
        }

        if state != params["state"]:
            send_message(
                client,
                "State mismatch. Expected: {} Received: {}".format(
                    state, params["state"]
                ),
            )
        elif "error" in params:
            send_message(client, params["error"])

        refresh_token = reddit.auth.authorize(params["code"])
        send_message(client, "Refresh token: {}".format(refresh_token))
        colormsg(refresh_token, fg.blue)
        if not reddit.user.me():
            colormsg(
                f"Unable to login to reddit. Please check {botfiles.prawconfig}", fg.red
            )
            exit(1)
except Exception as e:
    colormsg(f"Unable to login to reddit. Please check {botfiles.prawconfig}", fg.red)
    colormsg(f"{e}", fg.red)
finally:
    os.chdir(cwd)

pg = reddit.subreddit("itoxtestingfacility" if debug else "picturegame")

username = str(reddit.user.me())

donotreply = {
    "achievements-bot",
    username.lower(),
    "r-picturegame",
    "imreallycuriousbird",
}

api = "https://api.picturega.me"
