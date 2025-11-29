import feedparser
import os
import time
import urllib.parse
from datetime import datetime, timedelta
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential


def fetch_arxiv_papers(categories, max_results=20, since_date=None):
    base_url = "http://export.arxiv.org/api/query?"
    # Construct query: cat:cs.AI OR cat:cs.LG ...
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    
    # Sort by submittedDate descending
    query_params = {
        "search_query": cat_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    url = base_url + urllib.parse.urlencode(query_params)
    print(f"Fetching from ArXiv: {url}")
    feed = feedparser.parse(url)
    
    papers = []
    for entry in feed.entries:
        # Parse published date
        published_struct = entry.published_parsed
        published_dt = datetime.fromtimestamp(time.mktime(published_struct))
        
        # Filter by date if provided
        if since_date and published_dt <= since_date:
            print(f"  [SKIP] Old paper: {entry.title} ({published_dt})")
            continue

        paper = {
            "title": entry.title.replace("\n", " "),
            "link": entry.link,
            "abstract": entry.summary.replace("\n", " "),
            "published": entry.published,
            "authors": [author.name for author in entry.authors]
        }
        papers.append(paper)

    print(f"Fetched {len(papers)} papers.")
    return papers

def filter_papers_with_llm(papers, keywords, model_name):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not found. Skipping LLM filtering.")
        return papers # Fallback: return all or implement basic string matching

    endpoint = "https://models.inference.ai.azure.com"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    filtered_papers = []
    
    print(f"Filtering {len(papers)} papers with LLM...")

    for paper in papers:
        prompt = f"""
        User is interested in the following keywords/topics: {', '.join(keywords)}.
        
        Paper Title: {paper['title']}
        Abstract: {paper['abstract']}
        
        Rate the relevance of this paper to the user's interests on a scale from 0 to 10.
        0 = Not relevant at all
        10 = Highly relevant
        
        Reply with strictly the number denoting the relevance score.
        """

        try:
            response = client.complete(
                messages=[
                    SystemMessage(content="You are a research paper filter."),
                    UserMessage(content=prompt),
                ],
                model=model_name
            )
            
            content = response.choices[0].message.content.strip()
            try:
                score = int(content)
            except ValueError:
                # Try to find a number in the string if LLM is chatty
                import re
                match = re.search(r'\d+', content)
                if match:
                    score = int(match.group())
                else:
                    print(f"Warning: Could not extract score from response: {content}")
                    score = 0
            
            if score >= 7:
                print(f"  [KEEP] {paper['title']} (Score: {score})")
                filtered_papers.append(paper)
            else:
                print(f"  [SKIP] {paper['title']} (Score: {score})")
                
        except Exception as e:
            print(f"Error filtering paper '{paper['title']}': {e}")
            # On error, maybe keep it to be safe? Or skip. Let's keep it.
            filtered_papers.append(paper)
        
    print(f"Selected {len(filtered_papers)} relevant papers using {model_name}.")
    return filtered_papers

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    categories = config["arxiv"]["categories"]
    keywords = config["arxiv"]["keywords"]
    max_results = config["arxiv"]["max_results"]
    filter_model = config.get("models", {}).get("filter", "gpt-4o-mini")
    
    print("Fetching papers...")
    papers = fetch_arxiv_papers(categories, max_results)
    print(f"Fetched {len(papers)} papers.")
    
    print("Filtering papers...")
    relevant_papers = filter_papers_with_llm(papers, keywords, filter_model)
    print(f"Selected {len(relevant_papers)} relevant papers.")
    
    # For testing purposes
    for p in relevant_papers:
        print(f"- {p['title']}")
