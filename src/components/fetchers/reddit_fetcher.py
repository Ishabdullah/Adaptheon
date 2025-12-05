"""
Reddit Fetcher - Social Media and Community Discussions
Production-grade Reddit data retrieval
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class RedditFetcher(BaseFetcher):
    """
    Fetches trending posts and discussions from Reddit
    Excellent for: trending topics, community opinions, discussions
    """

    def _setup(self):
        self.base_url = "https://www.reddit.com"

    def fetch(self, query: str) -> FetchResult:
        """Search Reddit for trending posts"""
        try:
            # Extract subreddit if specified
            query_lower = query.lower()
            subreddit = None

            if "subreddit" in query_lower or "r/" in query_lower:
                # Extract subreddit name
                words = query.split()
                for word in words:
                    if word.startswith("r/"):
                        subreddit = word[2:]
                        break

            if subreddit:
                url = f"{self.base_url}/r/{subreddit}/hot.json"
            else:
                url = f"{self.base_url}/r/all/hot.json"

            params = {'limit': 3}

            # Reddit requires .json extension and returns JSON
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or 'data' not in data or not data['data'].get('children'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            # Get top post
            post = data['data']['children'][0]['data']
            title = post.get('title', 'No title')
            author = post.get('author', 'Unknown')
            score = post.get('score', 0)
            num_comments = post.get('num_comments', 0)
            subreddit_name = post.get('subreddit', 'Unknown')
            permalink = post.get('permalink', '')

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "title": title,
                    "author": author,
                    "score": score,
                    "comments": num_comments,
                    "subreddit": subreddit_name
                },
                summary=f"r/{subreddit_name}: {title} ({score} upvotes, {num_comments} comments)",
                confidence=0.75,
                source="reddit",
                url=f"https://www.reddit.com{permalink}"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
