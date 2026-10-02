import time
from collections import OrderedDict

from .Retry import retry

POLL_LIMIT = 100


class FifoSet:
    def __init__(self, size):
        self.size = size
        self._items = OrderedDict()

    def __contains__(self, item):
        return item in self._items

    def add(self, item):
        if item in self._items:
            return
        if len(self._items) >= self.size:
            self._items.popitem(last=False)
        self._items[item] = None


class RedditPoller:
    """
    Polls one or more reddit listings (newest first) and yields each item once, oldest first.
    Yields None after every poll that had nothing new
    """

    def __init__(self, *functions, interval=1):
        self.functions = functions
        self.interval = interval
        self.seenNames = FifoSet(POLL_LIMIT * 1000)

    def getLatest(self):
        while True:
            new = [item for item in self._poll() if item.name not in self.seenNames]
            new.sort(key=lambda item: getattr(item, "created_utc", 0))
            for item in new:
                self.seenNames.add(item.name)
                yield item
            yield None
            if not new:
                time.sleep(self.interval)

    def _poll(self):
        items = []
        for function in self.functions:
            items.extend(self._fetch(function))
        return items

    @staticmethod
    @retry
    def _fetch(function):
        # the 'before' parameter is not used on purpose, reddit returns nothing when
        # the item it refers to is deleted or comes from a different listing
        return list(function(limit=POLL_LIMIT)) or []
