"""
Checks rounds.yaml and hints.yaml for mistakes so they can be fixed before a round is won.
Run on its own with `python -m botterino.validate`
"""

import difflib
import os
import warnings

import ruamel.yaml
from geopy.point import Point
from sty import fg

from .Loader.loader import (
    IMAGE_EXTENSIONS,
    hintfile,
    imageSearchPath,
    load,
    resolveImagePath,
    roundfile,
)
from .Utils.color import colormsg

ERROR = "error"
WARNING = "warning"

KNOWN_FIELDS = {
    "title",
    "url",
    "path",
    "answer",
    "tolerance",
    "answers",
    "tolerances",
    "text",
    "similarity",
    "ignorecase",
    "manual",
    "message",
    "after",
    "series",
}

# reddit's limits
MAX_TITLE_LENGTH = 300
MAX_IMAGE_BYTES = 20 * 1024 * 1024
# room for '[Round 123456] '
ROUND_PREFIX_LENGTH = 15


def isNumber(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parsePoint(value):
    """returns a geopy Point or None if the value is not a coordinate"""
    if value is None or isinstance(value, bool):
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return Point(str(value))
    except (ValueError, TypeError):
        return None


def checkRound(r):
    """returns a list of (level, message) problems with a single round"""
    if not isinstance(r, dict):
        return [
            (
                ERROR,
                "is not a round. Each round needs fields like 'title:' indented by two spaces underneath its name",
            )
        ]

    problems = []
    error = lambda msg: problems.append((ERROR, msg))
    warn = lambda msg: problems.append((WARNING, msg))

    for field in r:
        if field not in KNOWN_FIELDS:
            close = difflib.get_close_matches(str(field), KNOWN_FIELDS, n=1)
            hint = f", did you mean '{close[0]}'?" if close else ""
            warn(f"unknown field '{field}' will be ignored{hint}")

    title = r.get("title")
    if title is None or not str(title).strip():
        error("'title' is missing")
    else:
        series = r.get("series")
        length = len(str(title)) + ROUND_PREFIX_LENGTH
        if series:
            length += len(str(series)) + 10
        if length > MAX_TITLE_LENGTH:
            error(
                f"title is too long, reddit titles are limited to {MAX_TITLE_LENGTH} characters including the round number"
            )

    url, path = r.get("url"), r.get("path")
    if url and path:
        error("has both 'url' and 'path', use only one")
    elif not url and not path:
        error("needs either a 'url' or an image 'path'")
    elif url and not isinstance(url, str):
        error("'url' should be text")
    elif path:
        fullpath = resolveImagePath(path)
        if not os.path.isfile(fullpath):
            where = (
                ""
                if os.path.isabs(os.path.expanduser(str(path)))
                else f" (looked in {', '.join(imageSearchPath())})"
            )
            error(f"image file '{path}' does not exist{where}")
        elif not fullpath.lower().endswith(IMAGE_EXTENSIONS):
            error(f"image '{fullpath}' should be one of {', '.join(IMAGE_EXTENSIONS)}")
        elif os.path.getsize(fullpath) > MAX_IMAGE_BYTES:
            error(f"image '{fullpath}' is larger than reddit's 20MB limit")

    answer, tolerance = r.get("answer"), r.get("tolerance")
    if answer is not None and parsePoint(answer) is None:
        error(
            f"answer '{answer}' is not a valid coordinate, use decimal format like 36.170439, -115.139889"
        )
    if tolerance is not None and (not isNumber(tolerance) or tolerance < 0):
        error(f"tolerance '{tolerance}' should be a positive number of meters")
    if answer is not None and tolerance is None:
        warn("has an 'answer' but no 'tolerance', guesses will not be checked")
    if tolerance is not None and answer is None:
        error("has a 'tolerance' but no 'answer'")

    answers, tolerances = r.get("answers"), r.get("tolerances")
    if answers is not None or tolerances is not None:
        if not isinstance(answers, list) or not answers:
            error("'answers' should be a list like ['12.34, 56.78', '-12.34, 98.76']")
        elif not isinstance(tolerances, list):
            error(
                "'tolerances' should be a list like [20, 60] with one tolerance per answer"
            )
        else:
            if len(answers) != len(tolerances):
                error(
                    f"has {len(answers)} answers but {len(tolerances)} tolerances, they must be the same"
                )
            for a in answers:
                if parsePoint(a) is None:
                    error(f"answer '{a}' in 'answers' is not a valid coordinate")
            for t in tolerances:
                if not isNumber(t) or t < 0:
                    error(
                        f"tolerance '{t}' in 'tolerances' should be a positive number of meters"
                    )
        if answer is not None:
            warn("has both 'answer' and 'answers', only 'answer' will be checked")

    text, similarity = r.get("text"), r.get("similarity")
    if text is not None and similarity is None:
        warn("has 'text' but no 'similarity', the text will not be checked")
    if similarity is not None:
        if not isNumber(similarity) or not 0 <= similarity <= 1:
            error(f"similarity '{similarity}' should be a number between 0.0 and 1.0")
        if text is None:
            warn("has 'similarity' but no 'text'")

    for field in ("manual", "ignorecase"):
        if field in r and not isinstance(r[field], bool):
            error(f"'{field}' should be true or false without quotes")

    for field in ("message", "after", "series"):
        if field in r and (r[field] is None or not str(r[field]).strip()):
            warn(f"'{field}' is empty")

    if r.get("manual") and answer is None and answers is None and text is None:
        warn("is 'manual' but has no answer, so there is nothing to check")

    return problems


def roundErrors(r):
    return [msg for level, msg in checkRound(r) if level == ERROR]


def _compose(file):
    """parse a yaml file, returns (node, error message)"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            return ruamel.yaml.YAML().compose(f), None
    except ruamel.yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def _topLevel(node):
    """returns [(key, line)] for the top level of a yaml mapping"""
    if node is None or not isinstance(node, ruamel.yaml.nodes.MappingNode):
        return None
    return [(k.value, k.start_mark.line + 1) for k, _ in node.value]


def _duplicates(entries):
    seen, dupes = set(), []
    for key, line in entries:
        if key in seen:
            dupes.append((key, line))
        seen.add(key)
    return dupes


def checkRoundsFile(file=roundfile):
    """
    returns (problems, keys) where problems is a list of (level, location, message)
    and keys is the list of round names in order
    """
    node, parseError = _compose(file)
    if parseError:
        return [
            (ERROR, os.path.basename(file), f"is not valid yaml:\n{parseError}")
        ], []
    entries = _topLevel(node)
    if node is not None and entries is None:
        return [
            (
                ERROR,
                os.path.basename(file),
                "should be a list of named rounds, see sample-rounds.yaml",
            )
        ], []
    entries = entries or []

    problems = []
    for key, line in _duplicates(entries):
        problems.append(
            (
                WARNING,
                f"'{key}' (line {line})",
                "has the same name as an earlier round, it will be lost. Give every round a unique name",
            )
        )

    data = load(file) or {}
    lines = {}
    for key, line in entries:
        lines.setdefault(key, line)
    for key, r in data.items():
        for level, msg in checkRound(r):
            problems.append((level, f"'{key}' (line {lines.get(key, '?')})", msg))
    return problems, list(data.keys())


def checkHintsFile(file=hintfile):
    node, parseError = _compose(file)
    if parseError:
        return [(ERROR, os.path.basename(file), f"is not valid yaml:\n{parseError}")]
    if node is None:
        return []
    if _topLevel(node) is None:
        return [
            (
                ERROR,
                os.path.basename(file),
                "should be a list of round names with hints, see sample-hints.yaml",
            )
        ]

    problems = []
    for key, value in (load(file) or {}).items():
        where = f"hints for '{key}'"
        hints = value.get("hints") if isinstance(value, dict) else None
        if not isinstance(hints, list):
            problems.append((ERROR, where, "should contain a 'hints:' list"))
            continue
        for hint in hints:
            if not isinstance(hint, dict):
                problems.append(
                    (ERROR, where, f"hint '{hint}' should have a 'time' and 'text'")
                )
                continue
            if not isNumber(hint.get("time")) or hint["time"] < 0:
                problems.append(
                    (
                        ERROR,
                        where,
                        f"hint time '{hint.get('time')}' should be a number of minutes",
                    )
                )
            if not hint.get("text"):
                problems.append(
                    (
                        WARNING,
                        where,
                        f"the {hint.get('time')}m hint has no text and will be skipped",
                    )
                )
    return problems


def report(problems):
    for level, where, msg in problems:
        if level == ERROR:
            colormsg(f"✖ {where} {msg}", fg.red)
        else:
            colormsg(f"⚠ {where} {msg}", fg.yellow)


def checkFiles(quiet=False):
    """
    validates rounds.yaml and hints.yaml and prints any problems
    returns True if there are no errors
    """
    problems, keys = checkRoundsFile()
    problems += checkHintsFile()
    errors = [p for p in problems if p[0] == ERROR]
    report(problems)
    if quiet and not problems:
        return True
    if errors:
        colormsg(
            f"Found {len(errors)} error(s), fix them before you win!",
            fg.red,
        )
    elif keys:
        upNext = f", next up: '{keys[0]}'"
        colormsg(f"✔ {len(keys)} round(s) ready{upNext}", fg.green)
    else:
        colormsg(f"No rounds queued yet, add some to {roundfile}", fg.yellow)
    return not errors


def main():
    raise SystemExit(0 if checkFiles() else 1)


if __name__ == "__main__":
    main()
