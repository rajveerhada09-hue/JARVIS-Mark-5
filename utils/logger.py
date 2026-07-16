import logging
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("JARVIS")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s | %(message)s"
)

file_handler = logging.FileHandler(
    "logs/jarvis.log",
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)