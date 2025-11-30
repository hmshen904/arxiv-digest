import feedparser
import urllib.parse
from datetime import datetime

from models import Paper


def fetch_arxiv_papers(
    categories: list[str],
    since_date: datetime,
    max_results: int = 1000,
) -> list[Paper]:
    """Fetch papers from arXiv API.
    
    Args:
        categories: List of arXiv categories (e.g., "cs.CR", "cs.LG").
        since_date: Only return papers submitted after this date.
        max_results: Maximum number of results to return.
    
    Returns:
        List of Paper objects.
    """
    base_url = "https://export.arxiv.org/api/query?"
    cat_query = "(" + " OR ".join([f"cat:{cat}" for cat in categories]) + ")"
    
    start_date = since_date.strftime("%Y%m%d%H%M")
    end_date = "999912312359"
    date_filter = f"submittedDate:[{start_date} TO {end_date}]"
    search_query = f"{cat_query} AND {date_filter}"
    
    query_params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    url = base_url + urllib.parse.urlencode(query_params)
    print(f"Fetching from arXiv: {url}")
    feed = feedparser.parse(url)
    
    papers = [Paper.from_arxiv_entry(entry) for entry in feed.entries]

    print(f"Fetched {len(papers)} papers from arXiv.")
    return papers


if __name__ == "__main__":
    from datetime import timedelta
    from utils import load_config
    
    config = load_config()
    
    categories = config["arxiv"]["categories"]
    max_results = 10
    since = datetime.now() - timedelta(days=7)
    
    print("Fetching papers...")
    papers = fetch_arxiv_papers(categories, since, max_results)
    
    for p in papers:
        print(f"- {p.title}")
