"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : parallel.py

PATH    : core\execution\parallel.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import threading

def run_parallel(pc_func, browser_func, data):
    t1 = threading.Thread(target=pc_func, args=(data,))
    t2 = threading.Thread(target=browser_func, args=(data,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()