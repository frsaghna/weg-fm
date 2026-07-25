"""
Frecency (Frequency + Recency) Engine for weg (Phase 8.3).
Tracks visited directories and calculates zoxide-style quick jump targets.
"""

import os
import json
import time

FRECENCY_PATH = os.path.expanduser("~/.config/weg/frecency.json")

class FrecencyTracker:
    def __init__(self, storage_path=FRECENCY_PATH, max_entries=500):
        self.storage_path = storage_path
        self.max_entries = max_entries
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Frecency] Save error: {e}")

    def record_visit(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return

        now = time.time()
        entry = self.data.get(path, {"count": 0, "last_visit": now})
        entry["count"] += 1
        entry["last_visit"] = now
        self.data[path] = entry

        if len(self.data) > self.max_entries:
            sorted_items = sorted(self.data.items(), key=lambda x: x[1].get("last_visit", 0), reverse=True)
            self.data = dict(sorted_items[:self.max_entries])

        self._save()

    def score(self, entry, now):
        count = entry.get("count", 1)
        last_visit = entry.get("last_visit", now)
        hours_ago = max(0.0, (now - last_visit) / 3600.0)
        return count / (1.0 + 0.25 * hours_ago)

    def query(self, fragment):
        if not fragment:
            return None

        frag_lower = fragment.lower().strip()
        now = time.time()
        best_path = None
        best_score = -1.0

        for path, entry in self.data.items():
            if not os.path.exists(path):
                continue

            basename = os.path.basename(path).lower()
            path_lower = path.lower()

            if frag_lower in basename or frag_lower in path_lower:
                sc = self.score(entry, now)
                if frag_lower in basename:
                    sc *= 2.0
                if sc > best_score:
                    best_score = sc
                    best_path = path

        return best_path
