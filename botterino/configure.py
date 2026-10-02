"""
Interactive setup, runs automatically the first time botterino is started.
Run it again at any time with `python -m botterino.configure`
"""

import os
import shutil
import sys
from configparser import ConfigParser

from sty import ef, fg, rs

DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), "botterino-config")
# remembers a custom config location
POINTER_FILE = os.path.join(os.path.expanduser("~"), ".botterino")
ENV_VAR = "BOTTERINO_CONFIG"

ACCENT = fg(214)
DIM = fg(245)


def _enableColor():
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    try:
        import colorama  # pylint: disable=import-outside-toplevel

        colorama.just_fix_windows_console()
    except (ImportError, AttributeError):
        if sys.platform == "win32":
            os.system("")
    return True


COLOR = _enableColor()


def paint(text, *styles):
    if not COLOR:
        return text
    return "".join(styles) + text + rs.all


def normalize(path):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path.strip())))


def configDir():
    """where botterino-config lives: $BOTTERINO_CONFIG, then ~/.botterino, then the default"""
    if os.environ.get(ENV_VAR):
        return normalize(os.environ[ENV_VAR])
    try:
        with open(POINTER_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
        if path:
            return normalize(path)
    except OSError:
        pass
    return DEFAULT_CONFIG_DIR


def isFirstRun():
    return (
        not os.environ.get(ENV_VAR)
        and not os.path.exists(POINTER_FILE)
        and not os.path.exists(DEFAULT_CONFIG_DIR)
    )


def ask(step, total, question, default, explanation=None):
    print()
    print(
        paint(f" {step}/{total} ", ef.bold, fg.black, "\033[48;5;214m")
        + " "
        + paint(question, ef.bold)
    )
    if explanation:
        print(paint(f"     {explanation}", DIM))
    try:
        answer = input(paint("     ❯ ", ACCENT) + paint(f"[{default}] ", DIM)).strip()
    except EOFError:
        answer = ""
    return answer or default


def askYesNo(step, total, question, default=True, explanation=None):
    hint = "Y/n" if default else "y/N"
    while True:
        answer = ask(step, total, question, hint, explanation)
        if answer == hint:
            return default
        if answer.lower() in ("y", "yes"):
            return True
        if answer.lower() in ("n", "no"):
            return False
        print(paint("     please answer y or n", fg.red))


def banner(title):
    width = 46
    print()
    print(paint("╭" + "─" * width + "╮", ACCENT))
    print(
        paint("│", ACCENT)
        + paint(f"  🤖 {title}".ljust(width - 1), ef.bold)
        + paint("│", ACCENT)
    )
    print(paint("╰" + "─" * width + "╯", ACCENT))
    print(paint("  Press enter to accept the [default] answer.", DIM))


def _readConfig(directory):
    parser = ConfigParser(interpolation=None)
    parser.read(os.path.join(directory, "config.ini"), encoding="utf-8")
    if not parser.has_section("config"):
        parser.add_section("config")
    return parser


def _moveFiles(old, new):
    for name in os.listdir(old):
        source, target = os.path.join(old, name), os.path.join(new, name)
        if os.path.exists(target):
            continue
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def runSetup(firstRun=False):
    """asks the user where things live, saves the answers and returns the config directory"""
    banner("Welcome to botterino!" if firstRun else "botterino setup")
    total = 3
    current = configDir()

    directory = normalize(
        ask(
            1,
            total,
            "Where should botterino keep its files?",
            current,
            "praw.ini, config.ini, rounds.yaml, hints.yaml and maps of guesses live here",
        )
    )
    os.makedirs(directory, exist_ok=True)
    if (
        directory != current
        and os.path.isdir(current)
        and os.listdir(current)
        and askYesNo(
            1,
            total,
            f"Copy your existing files from {current}?",
            True,
        )
    ):
        _moveFiles(current, directory)

    parser = _readConfig(directory)
    images = normalize(
        ask(
            2,
            total,
            "Which folder are your round images in?",
            parser.get("config", "images_dir", fallback="")
            or os.path.join(directory, "images"),
            "rounds can use 'path: photo.jpg' to upload an image from this folder",
        )
    )
    os.makedirs(images, exist_ok=True)

    openMap = askYesNo(
        3,
        total,
        "Open a map of everyone's guesses in your browser when a round ends?",
        parser.get("config", "open_map", fallback="true").lower() == "true",
        "the map is always saved to the maps folder either way",
    )

    parser.set("config", "images_dir", images)
    parser.set("config", "open_map", str(openMap).lower())
    with open(os.path.join(directory, "config.ini"), "w", encoding="utf-8") as f:
        parser.write(f)

    if os.environ.get(ENV_VAR):
        print(
            paint(
                f"\n  Note: ${ENV_VAR} is set and takes priority over this choice.",
                fg.yellow,
            )
        )
    if directory == DEFAULT_CONFIG_DIR:
        if os.path.exists(POINTER_FILE):
            os.remove(POINTER_FILE)
    else:
        with open(POINTER_FILE, "w", encoding="utf-8") as f:
            f.write(directory + "\n")

    print()
    print(paint("  ✔ All set!", fg.green, ef.bold))
    check = paint("✔", fg.green)
    print(f"  {check} files     {paint(directory, ACCENT)}")
    print(f"  {check} images    {paint(images, ACCENT)}")
    print(f"  {check} open map  {paint('yes' if openMap else 'no', ACCENT)}")
    print()
    print(paint("  Next steps:", ef.bold))
    print(
        f"   1. add your reddit app details to {paint(os.path.join(directory, 'praw.ini'), ACCENT)}"
    )
    print(
        f"   2. add rounds to {paint(os.path.join(directory, 'rounds', 'rounds.yaml'), ACCENT)}"
    )
    print(f"   3. run {paint('python -m botterino', ACCENT)} and go win a round!")
    print()
    return directory


def main():
    import botterino  # pylint: disable=import-outside-toplevel

    # importing botterino already ran the setup if this is the first run
    if not botterino.setupRan:
        botterino.prepare(runSetup())


if __name__ == "__main__":
    main()
