"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : priority_queue.py

PATH    : core\execution\priority_queue.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import heapq
import time

class PriorityQueueSystem:
    def __init__(self):
        self.queue = []

    def add(self, task, priority=5):
        heapq.heappush(self.queue, (priority, time.time(), task))

    def get_next(self):
        if self.queue:
            return heapq.heappop(self.queue)[2]
        return None