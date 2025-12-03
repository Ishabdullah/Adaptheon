import os
import json
from datetime import datetime, timedelta

from meta_core import MetaCognitiveCore


def prune_unknowns(days: int = 7):
    path = "data/cache/unknowns.json"
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return
    cutoff = datetime.utcnow() - timedelta(days=days)
    kept = []
    for entry in data:
        ts_str = entry.get("timestamp")
        if not ts_str:
            # keep newest-style entries only
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:
            continue
        if ts >= cutoff:
            kept.append(entry)
    with open(path, "w") as f:
        json.dump(kept, f, indent=2)


def tag_unknowns_with_time():
    """
    One-time migration helper: ensure unknown entries have a timestamp field.
    Called before pruning if needed.
    """
    path = "data/cache/unknowns.json"
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return
    changed = False
    now = datetime.utcnow().isoformat(timespec="seconds")
    for entry in data:
        if "timestamp" not in entry:
            entry["timestamp"] = now
            changed = True
    if changed:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def refresh_time_sensitive(core: MetaCognitiveCore):
    """
    Hook for refreshing very time-sensitive topics, if desired.
    Currently just a stub; you can later:
      - iterate over recent sports/office-holder queries
      - re-run Scout with ignore_cache=True
      - update memory/graph/vector entries.
    """
    # Example: nothing implemented yet, placeholder for future work.
    return


def main():
    core = MetaCognitiveCore()
    print("[Maintenance] Tagging unknowns with timestamps (if missing)...")
    tag_unknowns_with_time()
    print("[Maintenance] Pruning old unknowns (older than 7 days)...")
    prune_unknowns(days=7)
    print("[Maintenance] Refresh hook for time-sensitive topics (stub)...")
    refresh_time_sensitive(core)
    print("[Maintenance] Done.")


if __name__ == "__main__":
    main()
