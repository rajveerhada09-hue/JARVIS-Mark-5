import hashlib
import json
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("voice/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST = CACHE_DIR / "manifest.json"


class VoiceCacheManager:

    def __init__(self):
        if not MANIFEST.exists():
            MANIFEST.write_text("{}")

        self._load()

    def _load(self):
        try:
            with open(MANIFEST, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}

    def _save(self):
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def generate_hash(self, text, voice_id, model, emotion):
        raw = f"{voice_id}|{model}|{emotion}|{text}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_cached_file(self, hash_key):
        file = CACHE_DIR / f"{hash_key}.mp3"

        if file.exists():
            self.touch(hash_key)
            return file

        return None

    def save_cache(self, hash_key, text, voice_id, model, emotion):

        self.data[hash_key] = {
            "text": text,
            "voice": voice_id,
            "model": model,
            "emotion": emotion,
            "created": str(datetime.now()),
            "last_used": str(datetime.now()),
            "hits": 1,
        }

        self._save()

    def touch(self, hash_key):
        if hash_key not in self.data:
            return

        self.data[hash_key]["hits"] += 1
        self.data[hash_key]["last_used"] = str(datetime.now())
        self._save()

    def save_cached_file(
        self,
        hash_key,
        file_path,
        text,
        voice_id,
        model,
        emotion,
    ):

        target = CACHE_DIR / f"{hash_key}.mp3"

        if Path(file_path).resolve() != target.resolve():
            Path(file_path).replace(target)

        self.data[hash_key] = {
            "text": text,
            "voice": voice_id,
            "model": model,
            "emotion": emotion,
            "created": str(datetime.now()),
            "last_used": str(datetime.now()),
            "hits": 1,
            "file": target.name,
        }

        self._save()

        return target