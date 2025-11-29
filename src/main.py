import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from arxiv_fetcher import fetch_arxiv_papers, filter_papers_with_llm
from summarizer import summarize_papers
from issue_creator import create_issue
from github_client import GitHubClient
from utils import load_config

def create_openai_client(base_url):
    """Create and return an OpenAI client."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")
    
    print(f"Creating OpenAI client with base URL: {base_url}")
    return OpenAI(
        base_url=base_url,
        api_key=token,
    )


def main():
    load_dotenv()
    print("Starting ArXiv Paper Summarizer...")
    config = load_config()
    
    # Extract config values
    categories = config["arxiv"]["categories"]
    keywords = config["arxiv"]["keywords"]
    max_results = config["arxiv"]["max_results"]
    
    github_config = config["github"]
    usernames = github_config.get("usernames", [])
    issue_label = github_config.get("issue_label", "arxiv-summary")
    
    openai_base_url = config["llm_service"]["base_url"]
    filter_model = config["models"]["filter"]
    summarize_model = config["models"]["summarize"]
    
    # Create clients
    openai_client = create_openai_client(openai_base_url)
    github_client = GitHubClient()
    
    # 0. Determine start date
    last_run = github_client.get_last_issue_date(issue_label)
    if last_run:
        print(f"Last run found: {last_run}")
    else:
        print("No previous run found. Fetching latest papers (no date limit).")
    end_date = datetime.now()

    # 1. Fetch
    print("--- Step 1: Fetching Papers ---")
    papers = fetch_arxiv_papers(categories, max_results, since_date=last_run)
    if not papers:
        print("No new papers found.")
        return

    # 2. Filter (LLM)
    print("--- Step 2: Filtering Papers ---")
    relevant_papers = filter_papers_with_llm(papers, keywords, filter_model, openai_client)
    if not relevant_papers:
        print("No relevant papers found after filtering.")
        return

    # 3. Summarize
    print("--- Step 3: Summarizing Papers ---")
    summarized_papers = summarize_papers(relevant_papers, summarize_model, openai_client)

    # 4. Create Issue
    print("--- Step 4: Creating GitHub Issue ---")
    try:
        create_issue(github_client, summarized_papers, usernames, issue_label, last_run, end_date)
    except RuntimeError as e:
        print(f"Error: {e}")
        exit(1)
    
    print("Done!")

if __name__ == "__main__":
    main()
