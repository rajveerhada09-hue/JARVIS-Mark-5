"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : download_model.py

PATH    : download_model.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from huggingface_hub import snapshot_download
import os

def download_whisper_medium():

    print("\n[MODEL] Downloading Faster Whisper MEDIUM...")

    local_dir = os.path.join("models", "medium")

    snapshot_download(
        repo_id="Systran/faster-whisper-medium",
        local_dir=local_dir,
        local_dir_use_symlinks=False
    )

    print("\n✅ Model downloaded successfully at:", local_dir)


if __name__ == "__main__":
    download_whisper_medium()