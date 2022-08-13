from pathlib import Path
from ..config import roundfile, archivefile
import ruamel.yaml

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True

def dump(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
        
def append(data, file):
    with open(file, 'r', encoding='utf-8') as f:
        x = yaml.load(f)
    if not x:
        dump(data, file)
        return
    x.update(data)
    dump(x, file)

def load(file):
    with open(file, 'r', encoding='utf-8') as f:
        return yaml.load(f)

def getRound():
    x = load(roundfile)
    if not x:
        return None
    k = next(iter(x))
    top = x.pop(k)
    if x:
        dump(x, roundfile)
    else:
        open(roundfile, 'w', encoding='utf-8').close()
    y = load(archivefile) or {}
    y[k] = top
    dump(y, archivefile)
    return top
