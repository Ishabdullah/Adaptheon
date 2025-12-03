import os
import json
from datetime import datetime

from meta_core import MetaCognitiveCore


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024.0:
            return f"{size:.1f}{u}"
        size /= 1024.0
    return f"{size:.1f}TB"


def file_info(path: str):
    if not os.path.exists(path):
        return "missing"
    st = os.stat(path)
    return f"{human_size(st.st_size)} (modified {datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')})"


def main():
    core = MetaCognitiveCore()

    print("=== Adaptheon Status ===")
    print(f"- Memory layers: {list(core.memory.layers.keys())}")
    print(f"- Vector store file: {file_info('data/vector_store.json')}")
    print(f"- Graph memory file: {file_info('data/graph/memory_graph.json')}")
    print(f"- Knowledge cache file: {file_info('data/cache/knowledge_cache.json')}")
    print(f"- Unknowns log file: {file_info('data/cache/unknowns.json')}")

    # Basic external stack sanity checks (no heavy calls)
    checks = {
        "wikidata_endpoint": "https://query.wikidata.org/sparql",
        "openlibrary": "https://openlibrary.org",
        "tmdb": "https://api.themoviedb.org/3" if os.environ.get("TMDB_API_KEY") else None,
        "aviationstack": "https://api.aviationstack.com/v1" if os.environ.get("AVIATIONSTACK_API_KEY") else None,
        "opencorporates": "https://api.opencorporates.com/v0.4",
    }

    import requests

    print("
=== External endpoints (HEAD ping) ===")
    for name, url in checks.items():
        if not url:
            print(f"- {name}: skipped (no API key / not configured)")
            continue
        try:
            resp = requests.head(url, timeout=5)
            print(f"- {name}: {resp.status_code}")
        except Exception as e:
            print(f"- {name}: ERROR ({e})")


if __name__ == "__main__":
    main()
