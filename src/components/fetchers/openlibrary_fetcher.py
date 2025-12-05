"""
Open Library Fetcher - Book Information
Production-grade book metadata and search
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class OpenLibraryFetcher(BaseFetcher):
    """
    Fetches book information from Open Library
    Excellent for: book metadata, authors, ISBNs, availability
    """

    def _setup(self):
        self.search_url = "https://openlibrary.org/search.json"
        self.works_url = "https://openlibrary.org/works"
        self.authors_url = "https://openlibrary.org/authors"

    def fetch(self, query: str) -> FetchResult:
        """Search for books"""
        try:
            # Clean query
            search_term = query.replace("book", "").replace("author", "").strip()

            params = {
                'q': search_term,
                'limit': 1,
                'fields': 'key,title,author_name,first_publish_year,isbn,publisher,subject'
            }

            data = self._make_request(self.search_url, params=params)
            if not data or not data.get('docs'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            book = data['docs'][0]
            title = book.get('title', 'Unknown')
            authors = book.get('author_name', ['Unknown'])
            year = book.get('first_publish_year', 'Unknown')
            isbn = book.get('isbn', ['N/A'])[0] if book.get('isbn') else 'N/A'
            subjects = book.get('subject', [])[:3]  # First 3 subjects

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "isbn": isbn,
                    "subjects": subjects
                },
                summary=f"{title} by {', '.join(authors)} ({year})",
                confidence=0.85,
                source="openlibrary",
                url=f"https://openlibrary.org{book.get('key', '')}"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
