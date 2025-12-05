"""
TheSportsDB Fetcher - Sports Data and Scores
Production-grade sports information
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class TheSportsDBFetcher(BaseFetcher):
    """
    Fetches sports data from TheSportsDB
    Excellent for: teams, players, leagues, scores, events
    """

    def _setup(self):
        self.base_url = "https://www.thesportsdb.com/api/v1/json"
        # Free tier available with limited features
        # For production use: Set THESPORTSDB_API_KEY in .env

    def fetch(self, query: str) -> FetchResult:
        """Search for sports information"""
        try:
            query_lower = query.lower()

            # Free tier search (limited)
            if "team" in query_lower:
                return self._search_team(query)
            elif "league" in query_lower:
                return self._search_league(query)
            else:
                return self._search_team(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _search_team(self, query: str) -> FetchResult:
        """Search for sports teams"""
        # Free tier endpoint
        team_name = query.replace("team", "").strip()

        url = f"{self.base_url}/1/searchteams.php"
        params = {'t': team_name}

        data = self._make_request(url, params=params)
        if not data or not data.get('teams'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        team = data['teams'][0]
        name = team.get('strTeam', 'Unknown')
        league = team.get('strLeague', 'Unknown')
        sport = team.get('strSport', 'Unknown')
        stadium = team.get('strStadium', 'Unknown')
        formed = team.get('intFormedYear', 'Unknown')

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "name": name,
                "league": league,
                "sport": sport,
                "stadium": stadium,
                "formed": formed
            },
            summary=f"{name} ({sport}): {league}, plays at {stadium}",
            confidence=0.80,
            source="thesportsdb",
            url=f"https://www.thesportsdb.com/team/{team.get('idTeam', '')}"
        )

    def _search_league(self, query: str) -> FetchResult:
        """Search for leagues"""
        league_name = query.replace("league", "").strip()

        url = f"{self.base_url}/1/search_all_leagues.php"
        params = {'s': league_name}

        data = self._make_request(url, params=params)
        if not data or not data.get('countries'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        # Get first league
        league = data['countries'][0] if data.get('countries') else {}
        name = league.get('strLeague', 'Unknown')
        sport = league.get('strSport', 'Unknown')

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "name": name,
                "sport": sport
            },
            summary=f"{name} ({sport})",
            confidence=0.75,
            source="thesportsdb"
        )
