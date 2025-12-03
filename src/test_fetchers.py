from components.fetchers.finance_fetcher import FinanceFetcher
from components.fetchers.weather_fetcher import WeatherFetcher
from components.fetchers.rss_fetcher import RSSFetcher


def main():
    print("=== FinanceFetcher test ===")
    fin = FinanceFetcher()
    print(fin.fetch("AAPL"))
    print(fin.fetch("bitcoin"))

    print("=== WeatherFetcher test ===")
    # Example: near Wethersfield, CT
    w = WeatherFetcher()
    print(w.fetch("41.71,-72.65"))

    print("=== RSSFetcher test ===")
    rss = RSSFetcher(
        feeds=[
            "https://www.reuters.com/rssFeed/worldNews",
            "https://apnews.com/apf-topnews?format=rss",
        ]
    )
    print(rss.fetch("bitcoin"))


if __name__ == "__main__":
    main()
