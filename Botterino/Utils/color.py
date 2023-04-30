from sty import fg
import random

badColors = [0, 16, 17, 18, 22, 52, 88, 90] + list(range(232, 256))


def randomColor():
    color = random.randrange(256)
    while color in badColors:
        color = random.randrange(256)
    return fg(color)


def getColorFromAuthor(author):
    seed = hash(author)
    random.seed(seed)
    color = random.randrange(256)
    while color in badColors:
        color = (color + 1) % 256
    return fg(color)


def colormsg(message, color=None, author=None):
    if not color:
        color = randomColor()
    if author:
        color = getColorFromAuthor(author)
    print(f"{color}{message}{fg.rs}")
