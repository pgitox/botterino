import os

import ruamel.yaml

from .. import botfiles

roundfile = botfiles.rounds
archivefile = botfiles.archive
hintfile = botfiles.hintfile

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True


def dump(data, file):
    tmp = f"{file}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    # atomic so a crash mid-write never wipes the round file
    os.replace(tmp, file)


def load(file):
    with open(file, "r", encoding="utf-8") as f:
        return yaml.load(f)


def append(data, file):
    x = load(file)
    if not x:
        dump(data, file)
        return
    x.update(data)
    dump(x, file)


def peekRound():
    """returns (key, round) of the next round without removing it, or None if there are no rounds"""
    x = load(roundfile)
    if not x:
        return None
    k = next(iter(x))
    return k, x[k]


def getRound():
    """removes the next round from the round file, archives it and returns (key, round)"""
    x = load(roundfile)
    if not x:
        return None
    k = next(iter(x))
    top = x.pop(k)
    if x:
        dump(x, roundfile)
    else:
        open(roundfile, "w", encoding="utf-8").close()
    archive = load(archivefile) or {}
    archiveKey, n = k, 2
    # never overwrite an older round in the archive that has the same name
    while archiveKey in archive:
        archiveKey = f"{k}_{n}"
        n += 1
    archive[archiveKey] = top
    dump(archive, archivefile)
    return k, top


def loadHints(key):
    hints = (load(hintfile) or {}).get(key) or {}
    return hints.get("hints") or []


def imageSearchPath():
    return [botfiles.imagesdir, botfiles.roundsdir, os.getcwd()]


def resolveImagePath(path):
    """
    absolute paths are used as is
    relative paths are looked up in the images folder, then the rounds folder, then the current directory
    returns the first existing match, or the path in the images folder if there is none
    """
    path = os.path.expanduser(os.path.expandvars(str(path).strip()))
    if os.path.isabs(path):
        return path
    candidates = [os.path.join(d, path) for d in imageSearchPath()]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return os.path.abspath(candidates[0])
