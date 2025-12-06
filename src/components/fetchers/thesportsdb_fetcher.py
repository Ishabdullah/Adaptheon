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

            # IDENTITY QUERIES: quarterback, coach, pitcher, player, etc.
            identity_keywords = [
                "quarterback", "qb", "pitcher", "coach", "manager",
                "player", "who is", "starting", "starter", "captain"
            ]

            if any(keyword in query_lower for keyword in identity_keywords):
                # This is a roster/identity query
                return self._fetch_roster_info(query)

            # Team searches
            elif "team" in query_lower:
                return self._search_team(query)

            # League searches
            elif "league" in query_lower:
                return self._search_league(query)

            # Default to team search
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

    def _fetch_roster_info(self, query: str) -> FetchResult:
        """
        Fetch roster/identity information (quarterback, coach, players).
        Example queries:
        - "Who is the quarterback for the New York Giants?"
        - "Who is the coach of the Lakers?"
        - "Starting pitcher for the Yankees"
        """
        query_lower = query.lower()

        # Extract team name from query
        # Try to identify common team names
        team_names = [
            "giants", "cowboys", "patriots", "steelers", "packers",
            "lakers", "celtics", "warriors", "heat", "bulls",
            "yankees", "red sox", "dodgers", "mets", "cubs",
        ]

        team_found = None
        for team in team_names:
            if team in query_lower:
                team_found = team
                break

        if not team_found:
            # Try to extract from "for the X" or "of the X" patterns
            import re
            match = re.search(r'(?:for|of) (?:the )?([a-z\s]+?)(?:\?|$)', query_lower)
            if match:
                team_found = match.group(1).strip()

        if not team_found:
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                summary="Could not identify team name in query. Please specify the team.",
                confidence=0.0,
                source="thesportsdb"
            )

        # Attempt to get team info
        url = f"{self.base_url}/1/searchteams.php"
        params = {'t': team_found}

        data = self._make_request(url, params=params)

        if not data or not data.get('teams'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                summary=f"Could not find roster information for '{team_found}'. "
                        f"TheSportsDB free tier has limited roster data. "
                        f"Consider checking ESPN or team official website.",
                confidence=0.3,
                source="thesportsdb"
            )

        team = data['teams'][0]
        team_name = team.get('strTeam', 'Unknown')
        league = team.get('strLeague', 'Unknown')
        sport = team.get('strSport', 'Unknown')

        # Free tier doesn't provide current roster data via API
        # Return team info with suggestion to check other sources
        summary = (
            f"{team_name} ({sport}, {league}). "
            f"Roster information (quarterbacks, coaches, etc.) requires premium API access "
            f"or checking ESPN/official team sources for current data."
        )

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "team": team_name,
                "league": league,
                "sport": sport,
                "note": "Roster data requires premium access"
            },
            summary=summary,
            confidence=0.50,  # Lower confidence since we can't answer the specific identity question
            source="thesportsdb",
            url=f"https://www.thesportsdb.com/team/{team.get('idTeam', '')}"
        )
