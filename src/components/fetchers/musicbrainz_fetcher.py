"""
MusicBrainz Fetcher - Music Metadata
Production-grade music encyclopedia
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class MusicBrainzFetcher(BaseFetcher):
    """
    Fetches music information from MusicBrainz
    Excellent for: artists, albums, recordings, labels
    """

    def _setup(self):
        self.base_url = "https://musicbrainz.org/ws/2"
        self.session.headers.update({
            'User-Agent': 'Adaptheon/2.0 (Educational Research System)'
        })

    def fetch(self, query: str) -> FetchResult:
        """Search for music information"""
        try:
            query_lower = query.lower()

            # Determine search type
            if "artist" in query_lower:
                return self._search_artist(query)
            elif "album" in query_lower:
                return self._search_album(query)
            else:
                # Default to artist search
                return self._search_artist(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _search_artist(self, query: str) -> FetchResult:
        """Search for artists"""
        search_term = query.replace("artist", "").strip()

        url = f"{self.base_url}/artist"
        params = {
            'query': search_term,
            'fmt': 'json',
            'limit': 1
        }

        data = self._make_request(url, params=params)
        if not data or not data.get('artists'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        artist = data['artists'][0]
        name = artist.get('name', 'Unknown')
        country = artist.get('country', 'Unknown')
        life_span = artist.get('life-span', {})
        begin = life_span.get('begin', 'Unknown')
        disambiguation = artist.get('disambiguation', '')

        summary_parts = [name]
        if country != 'Unknown':
            summary_parts.append(f"from {country}")
        if begin != 'Unknown':
            summary_parts.append(f"active since {begin}")
        if disambiguation:
            summary_parts.append(f"({disambiguation})")

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "name": name,
                "country": country,
                "active_since": begin,
                "type": artist.get('type', 'Unknown'),
                "disambiguation": disambiguation
            },
            summary=", ".join(summary_parts),
            confidence=0.80,
            source="musicbrainz",
            url=f"https://musicbrainz.org/artist/{artist.get('id', '')}"
        )

    def _search_album(self, query: str) -> FetchResult:
        """Search for albums/releases"""
        search_term = query.replace("album", "").strip()

        url = f"{self.base_url}/release"
        params = {
            'query': search_term,
            'fmt': 'json',
            'limit': 1
        }

        data = self._make_request(url, params=params)
        if not data or not data.get('releases'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        release = data['releases'][0]
        title = release.get('title', 'Unknown')
        date = release.get('date', 'Unknown')
        artist_credit = release.get('artist-credit', [])
        artist_name = artist_credit[0].get('name', 'Unknown') if artist_credit else 'Unknown'

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "title": title,
                "artist": artist_name,
                "release_date": date,
                "country": release.get('country', 'Unknown')
            },
            summary=f"{title} by {artist_name} ({date})",
            confidence=0.80,
            source="musicbrainz",
            url=f"https://musicbrainz.org/release/{release.get('id', '')}"
        )
