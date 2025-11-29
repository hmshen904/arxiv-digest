import feedparser
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta


from utils import call_with_retry


RELEVANCE_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "description": "Relevance score from 0-10"
        }
    },
    "required": ["score"],
    "additionalProperties": False
}


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

def filter_papers_with_llm(papers, keywords, model_name, client):
    filtered_papers = []
    
    print(f"Filtering {len(papers)} papers with LLM...")

    for paper in papers:
        prompt = f"""Rate the relevance of this paper to the user's interests.

User's interests: {', '.join(keywords)}

Paper Title: {paper['title']}
Abstract: {paper['abstract']}

Return a score from 0-10 where 0 = not relevant, 10 = highly relevant."""

        try:
            response = call_with_retry(lambda: client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a research paper filter."},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "relevance_score",
                        "strict": True,
                        "schema": RELEVANCE_SCORE_SCHEMA
                    }
                }
            ))
            
            result = json.loads(response.choices[0].message.content)
            score = result["score"]
            
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
    import os
    from openai import OpenAI
    from dotenv import load_dotenv
    from utils import load_config
    
    load_dotenv()
    config = load_config()
    
    categories = config["arxiv"]["categories"]
    keywords = config["arxiv"]["keywords"]
    max_results = config["arxiv"]["max_results"]
    filter_model = config["models"]["filter"]
    base_url = config["llm_service"]["base_url"]
    
    client = OpenAI(base_url=base_url, api_key=os.environ.get("GITHUB_TOKEN"))
    
    print("Fetching papers...")
    papers = fetch_arxiv_papers(categories, max_results)
    print(f"Fetched {len(papers)} papers.")
    
    print("Filtering papers...")
    relevant_papers = filter_papers_with_llm(papers, keywords, filter_model, client)
    print(f"Selected {len(relevant_papers)} relevant papers.")
    
    # For testing purposes
    for p in relevant_papers:
        print(f"- {p['title']}")
