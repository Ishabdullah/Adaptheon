import requests
from bs4 import BeautifulSoup
import re
import string
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

class WikipediaFetcher(BaseFetcher):
    def __init__(self):
        self.headers = {
            "User-Agent": "Adaptheon/1.0 (Educational Project; Python/3)"
        }

    def _sanitize_topic(self, query: str) -> str:
        cleaned = query.strip()
        cleaned = cleaned.strip(string.punctuation)
        return cleaned

    def _clean_text(self, text: str, max_len: int = 400) -> str:
        # Remove citation markers like [1], [2]
        text = re.sub(r"\[\d+\]", "", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        # Keep only basic ASCII (letters, digits, punctuation, spaces)
        text = "".join(ch for ch in text if ch in string.printable)
        text = text.strip()
        # Truncate long paragraphs
        if len(text) > max_len:
            text = text[:max_len].rstrip() + "..."
        return text

    def fetch(self, query: str) -> Optional[FetchResult]:
        topic = self._sanitize_topic(query)
        if not topic:
            return None

        formatted = topic.replace(" ", "_")
        url = "https://en.wikipedia.org/wiki/{}".format(formatted)
        print("    [Wikipedia] Fetching: {}".format(url))

        try:
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code == 404:
                print("    [Wikipedia] Article not found (404)")
                return None
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            content = soup.find(id="mw-content-text")
            if not content:
                print("    [Wikipedia] No content block found")
                return None

            for p in content.find_all("p"):
                raw = p.get_text(strip=True)
                if len(raw) < 80:
                    continue
                cleaned = self._clean_text(raw)
                if len(cleaned) < 40:
                    continue
                print("    [Wikipedia] Extracted summary.")
                return FetchResult(
                    query=query,
                    summary=cleaned,
                    source=FetchSource.WIKIPEDIA,
                    confidence=0.85,
                    url=url,
                )

            print("    [Wikipedia] No substantial paragraph found")
            return None

        except requests.RequestException as e:
            print("    [Wikipedia] Network error: {}".format(e))
            return None
        except Exception as e:
            print("    [Wikipedia] Parse error: {}".format(e))
            return None
