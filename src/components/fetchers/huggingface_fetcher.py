"""
Hugging Face Hub Fetcher - AI Models and Datasets
Production-grade ML model and dataset search
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class HuggingFaceFetcher(BaseFetcher):
    """
    Fetches models and datasets from Hugging Face Hub
    Excellent for: AI models, datasets, model cards, trending ML
    """

    def _setup(self):
        self.api_base = "https://huggingface.co/api"

    def fetch(self, query: str) -> FetchResult:
        """Search Hugging Face for models or datasets"""
        try:
            query_lower = query.lower()

            # Determine if searching for model or dataset
            if "dataset" in query_lower:
                return self._search_datasets(query)
            else:
                return self._search_models(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _search_models(self, query: str) -> FetchResult:
        """Search for models"""
        search_term = query.replace("model", "").strip()

        url = f"{self.api_base}/models"
        params = {
            'search': search_term,
            'limit': 1,
            'sort': 'downloads'
        }

        data = self._make_request(url, params=params)
        if not data or not isinstance(data, list) or len(data) == 0:
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        model = data[0]
        model_id = model.get('id', 'Unknown')
        downloads = model.get('downloads', 0)
        likes = model.get('likes', 0)
        tags = model.get('tags', [])[:5]  # First 5 tags

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "model_id": model_id,
                "downloads": downloads,
                "likes": likes,
                "tags": tags
            },
            summary=f"{model_id}: {downloads:,} downloads, {likes} likes. Tags: {', '.join(tags[:3])}",
            confidence=0.85,
            source="huggingface",
            url=f"https://huggingface.co/{model_id}"
        )

    def _search_datasets(self, query: str) -> FetchResult:
        """Search for datasets"""
        search_term = query.replace("dataset", "").strip()

        url = f"{self.api_base}/datasets"
        params = {
            'search': search_term,
            'limit': 1,
            'sort': 'downloads'
        }

        data = self._make_request(url, params=params)
        if not data or not isinstance(data, list) or len(data) == 0:
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        dataset = data[0]
        dataset_id = dataset.get('id', 'Unknown')
        downloads = dataset.get('downloads', 0)
        likes = dataset.get('likes', 0)

        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "dataset_id": dataset_id,
                "downloads": downloads,
                "likes": likes
            },
            summary=f"{dataset_id}: {downloads:,} downloads, {likes} likes",
            confidence=0.85,
            source="huggingface",
            url=f"https://huggingface.co/datasets/{dataset_id}"
        )
