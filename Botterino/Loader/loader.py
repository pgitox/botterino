from pathlib import Path
from ..config import roundfile, archivefile
import ruamel.yaml

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True

rounds = Path(roundfile)
archive = Path(archivefile)

def getRound():
    x = yaml.load(rounds)
    if not x:
        return None
    k = next(iter(x))
    top = x.pop(k)
    if x:
        yaml.dump(x, rounds)
    else:
        open(rounds, 'w').close()
    y = yaml.load(archive) or {}
    y[k] = top
    yaml.dump(y, archive)
    return top