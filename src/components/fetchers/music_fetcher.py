import requests
from typing import Dict, Any, Optional, List


class MusicFetcher:
    """
    Music domain fetcher.
    Uses MusicBrainz search API for recordings (tracks) and artists.
    """

    def __init__(self):
        self.base = "https://musicbrainz.org/ws/2"
        self.headers = {
            "User-Agent": "Adaptheon/1.0 (on-device truth engine)"
        }

    def _search_recording(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        url = self.base + "/recording"
        params = {
            "query": query,
            "fmt": "json",
            "limit": limit,
        }
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        recs = data.get("recordings") or []
        return recs[:limit]

    def _search_artist(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        url = self.base + "/artist"
        params = {
            "query": query,
            "fmt": "json",
            "limit": limit,
        }
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        arts = data.get("artists") or []
        return arts[:limit]

    def _format_recording(self, recs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not recs:
            return None
        r = recs[0]
        title = r.get("title") or ""
        length_ms = r.get("length")
        length_part = ""
        if isinstance(length_ms, int) and length_ms > 0:
            secs = length_ms // 1000
            mins = secs // 60
            rem = secs % 60
            length_part = f" ({mins}:{rem:02d})"
        artists = r.get("artist-credit") or []
        names = []
        for ac in artists:
            art = ac.get("artist") or {}
            nm = art.get("name")
            if nm:
                names.append(nm)
        artist_part = ""
        if names:
            artist_part = " by " + ", ".join(names)
        releases = r.get("releases") or []
        release_title = releases[0].get("title") if releases else None
        release_part = ""
        if release_title:
            release_part = f" on the release '{release_title}'"
        summary = f"{title}{length_part}{artist_part}{release_part}."
        mbid = r.get("id")
        url = f"https://musicbrainz.org/recording/{mbid}" if mbid else None
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.86,
            "url": url,
            "metadata": {
                "source": "musicbrainz",
                "type": "recording",
                "mbid": mbid,
                "artists": names,
                "release": release_title,
            },
        }

    def _format_artist(self, arts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not arts:
            return None
        a = arts[0]
        name = a.get("name") or ""
        country = a.get("country")
        country_part = f" from {country}" if country else ""
        disambig = a.get("disambiguation") or ""
        dis_part = f" ({disambig})" if disambig else ""
        summary = f"{name}{dis_part}{country_part} is a musical artist in the MusicBrainz database."
        mbid = a.get("id")
        url = f"https://musicbrainz.org/artist/{mbid}" if mbid else None
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.8,
            "url": url,
            "metadata": {
                "source": "musicbrainz",
                "type": "artist",
                "mbid": mbid,
                "country": country,
            },
        }

    def fetch(self, query: str) -> Dict[str, Any]:
        """
        High-level music fetch: try recordings (tracks) then artists.
        """
        recs = self._search_recording(query, limit=3)
        formatted_rec = self._format_recording(recs or [])
        if formatted_rec:
            return formatted_rec

        arts = self._search_artist(query, limit=3)
        formatted_art = self._format_artist(arts or [])
        if formatted_art:
            return formatted_art

        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
