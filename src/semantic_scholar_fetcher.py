import requests
import time
from datetime import datetime
from models import Paper


SEMANTIC_SCHOLAR_BULK_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"


def fetch_semantic_scholar_papers(
    categories: list[str] | None,
    since_date: datetime,
    max_results: int = 1000,
) -> list[Paper]:
    """Fetch papers from Semantic Scholar bulk search API.
    
    Args:
        categories: List of fields of study (e.g., "Computer Science").
        since_date: Only return papers published after this date.
        max_results: Maximum number of results to return.
    
    Returns:
        List of Paper objects.
    """
    if not categories:
        print("Semantic Scholar requires categories (fields of study). Skipping.")
        return []
    
    papers = []
    fields = "title,url,abstract,authors,publicationDate,fieldsOfStudy,openAccessPdf"
    year = since_date.strftime("%Y-%m-%d")
    
    # Build fields of study filter
    fos_filter = "|".join(categories)
    
    params = {
        "fields": fields,
        "publicationDateOrYear": f"{year}:",
        "fieldsOfStudy": fos_filter,
    }
    
    print(f"Fetching from Semantic Scholar (bulk): {', '.join(categories)} since {year}")
    
    max_retries = 3
    base_delay = 2.0
    token = None
    
    while len(papers) < max_results:
        if token:
            params["token"] = token
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(SEMANTIC_SCHOLAR_BULK_API_URL, params=params, timeout=30)
                
                if response.status_code == 429:
                    if attempt == max_retries:
                        print(f"Rate limited by Semantic Scholar after {max_retries} retries.")
                        return papers
                    retry_after = response.headers.get("Retry-After", base_delay * (2 ** attempt))
                    delay = float(retry_after)
                    print(f"Rate limited. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as e:
                if attempt == max_retries:
                    print(f"Error fetching from Semantic Scholar: {e}")
                    return papers
                time.sleep(base_delay * (2 ** attempt))
        else:
            break
        
        results = data.get("data", [])
        if not results:
            break
        
        # Normalize categories to lowercase for comparison
        categories_lower = {c.lower() for c in categories}
        
        for item in results:
            if not item.get("abstract"):
                continue
            
            # Filter by fieldsOfStudy (API filtering is unreliable for new papers)
            item_fields = item.get("fieldsOfStudy") or []
            item_fields_lower = {f.lower() for f in item_fields}
            if not item_fields_lower & categories_lower:
                continue
            
            papers.append(Paper.from_semantic_scholar(item))
            if len(papers) >= max_results:
                break
        
        # Get continuation token for next page
        token = data.get("token")
        if not token:
            break
        
        time.sleep(1.0)
    
    print(f"Fetched {len(papers)} papers from Semantic Scholar.")
    return papers[:max_results]


if __name__ == "__main__":
    from datetime import timedelta
    
    since = datetime.now() - timedelta(days=7)
    
    papers = fetch_semantic_scholar_papers(
        categories=["Computer Science"],
        since_date=since,
        max_results=10,
    )
    
    for p in papers:
        print(f"- {p.title}")
