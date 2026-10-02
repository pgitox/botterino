import os
import random
import sys
import threading
import zlib

from sty import fg

from .. import settings

# halo calls colorama.init() when it is imported. On windows that wraps stdout in a
# converter which only understands 16 colors, mangling the 256 color codes used here
# and leaking hyperlink escape codes. Import it first, then undo the wrapping
import halo  # noqa: F401  # pylint: disable=unused-import

try:
    import colorama

    colorama.deinit()
    # enables native ANSI support on windows 10+, falls back to conversion on older windows
    colorama.just_fix_windows_console()
except (ImportError, AttributeError):
    if sys.platform == "win32":
        os.system("")

for stream in (sys.stdout, sys.stderr):
    try:
        # never crash printing emoji to a console or file that cannot encode them
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

badColors = [0, 16, 17, 18, 22, 52, 88, 90] + list(range(232, 256))
goodColors = [c for c in range(256) if c not in badColors]

printLock = threading.Lock()


def _enabled(option, envDisable=None):
    value = settings.get(option, "auto").strip().lower()
    if value in ("always", "true", "yes", "on"):
        return True
    if value in ("never", "false", "no", "off"):
        return False
    if envDisable and os.environ.get(envDisable):
        return False
    return sys.stdout.isatty()


useColor = _enabled("color", "NO_COLOR")
# OSC 8 links show up as garbage on the legacy windows console
useHyperlinks = _enabled("hyperlinks") and (
    sys.platform != "win32" or "WT_SESSION" in os.environ
)


def randomColor():
    return fg(random.choice(goodColors))


def getColorFromAuthor(author):
    """a color that is the same for an author every time botterino runs"""
    return fg(goodColors[zlib.crc32(author.lower().encode()) % len(goodColors)])


def hyperlink(alias, url):
    if not useHyperlinks:
        return alias
    return f"\u001b]8;;{url}\u001b\\{alias}\u001b]8;;\u001b\\"


def colormsg(message, color=None, author=None):
    if author:
        color = getColorFromAuthor(author)
    elif not color:
        color = randomColor()
    with printLock:
        if useColor:
            print(f"{color}{message}{fg.rs}", flush=True)
        else:
            print(message, flush=True)
