"""Repeated-tool detection."""

import json
from collections import deque


class RepeatToolGuard:
    def __init__(self, threshold=3):
        self.threshold = threshold
        self._history = deque(maxlen=max(threshold, 1))

    def record(self, name, arguments):
        signature = json.dumps({"name": name, "arguments": arguments},
                               sort_keys=True, ensure_ascii=False)
        self._history.append(signature)
        return len(self._history) >= self.threshold and len(set(self._history)) == 1

    def reset(self):
        self._history.clear()
