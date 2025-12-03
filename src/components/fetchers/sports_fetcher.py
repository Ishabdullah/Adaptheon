import requests
from typing import Dict, Any, Optional


class SportsFetcher:
    """
    Sports stack: primarily ESPN NFL scoreboard JSON for completed games.
    Designed for questions like 'who won the Giants game'.
    """

    def __init__(self):
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports"
        # TheSportsDB placeholder; can be expanded later.
        self.thesportsdb_base = "https://www.thesportsdb.com/api/v1/json"

    def _fetch_espn_nfl_scoreboard(self) -> Optional[Dict[str, Any]]:
        url = f"{self.espn_base}/football/nfl/scoreboard"
        try:
            resp = requests.get(url, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except Exception:
            return None

    def _find_team_game(self, data: Dict[str, Any], team_hint: str) -> Optional[Dict[str, Any]]:
        events = data.get("events", [])
        hint = team_hint.lower()
        for ev in events:
            competitions = ev.get("competitions") or []
            if not competitions:
                continue
            comp = competitions[0]
            competitors = comp.get("competitors") or []
            teams = []
            for c in competitors:
                tinfo = c.get("team") or {}
                name = tinfo.get("displayName") or ""
                abbr = tinfo.get("abbreviation") or ""
                teams.append(
                    {
                        "name": name,
                        "abbr": abbr,
                        "score": c.get("score"),
                        "winner": bool(c.get("winner")),
                    }
                )
            joined_names = " ".join([t["name"] + " " + t["abbr"] for t in teams]).lower()
            if hint in joined_names:
                return {
                    "event": ev,
                    "teams": teams,
                    "status": comp.get("status") or {},
                }
        return None

    def _format_game_summary(self, game: Dict[str, Any]) -> str:
        teams = game["teams"]
        status = game["status"]
        winners = [t for t in teams if t["winner"]]
        losers = [t for t in teams if not t["winner"]]

        if winners and losers:
            w = winners[0]
            l = losers[0]
            winner_name = w["name"]
            loser_name = l["name"]
            w_score = w["score"]
            l_score = l["score"]
            prefix = f"{winner_name} defeated {loser_name}"
            score_part = f" by a score of {w_score} to {l_score}"
        else:
            # Fallback if winner not set yet
            names = " vs. ".join([t["name"] for t in teams])
            prefix = f"The game between {names} has not yet completed"
            score_part = ""

        comp_status = status.get("type", {})
        detail = comp_status.get("detail") or status.get("displayClock") or ""
        if detail:
            detail_part = f" (status: {detail})"
        else:
            detail_part = ""

        return prefix + score_part + detail_part + "."

    def fetch_result(self, query: str) -> Dict[str, Any]:
        """
        Attempts to answer 'who won the X game' style questions for NFL.
        """
        # Extract a rough team hint from the query
        q_lower = query.lower()
        hint = q_lower
        # Simple heuristic: if 'giants' etc. present, use that
        for token in ["giants", "patriots", "jets", "cowboys", "eagles", "bills", "dolphins"]:
            if token in q_lower:
                hint = token
                break

        data = self._fetch_espn_nfl_scoreboard()
        if not data:
            return {"status": "NOT_FOUND", "summary": "", "confidence": 0.0, "url": None, "metadata": {}}

        game = self._find_team_game(data, hint)
        if not game:
            return {"status": "NOT_FOUND", "summary": "", "confidence": 0.0, "url": None, "metadata": {}}

        summary = self._format_game_summary(game)
        # ESPN event link if available
        ev = game["event"]
        links = ev.get("links") or []
        url = None
        for ln in links:
            if ln.get("href"):
                url = ln["href"]
                break

        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.88,
            "url": url,
            "metadata": {
                "provider": "espn",
                "league": "nfl",
                "event_id": ev.get("id"),
            },
        }
