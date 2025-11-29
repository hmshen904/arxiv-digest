import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
from arxiv_fetcher import fetch_arxiv_papers, filter_papers_with_llm
from summarizer import summarize_papers
from issue_creator import create_issue, get_last_issue_date


def load_and_validate_config():
    """Load config.yaml and validate required fields."""
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Validate arxiv section
    if "arxiv" not in config:
        raise ValueError("Config missing 'arxiv' section")
    arxiv = config["arxiv"]
    if "categories" not in arxiv or not arxiv["categories"]:
        raise ValueError("Config missing 'arxiv.categories'")
    if "keywords" not in arxiv or not arxiv["keywords"]:
        raise ValueError("Config missing 'arxiv.keywords'")
    if "max_results" not in arxiv:
        raise ValueError("Config missing 'arxiv.max_results'")
    
    # Validate github section
    if "github" not in config:
        raise ValueError("Config missing 'github' section")
    github = config["github"]
    if "repository" not in github or not github["repository"]:
        raise ValueError("Config missing 'github.repository'")
    
    # Validate models section (with defaults)
    if "models" not in config:
        config["models"] = {}
    config["models"].setdefault("filter", "gpt-5-mini")
    config["models"].setdefault("summarize", "gpt-5")
    
    return config


def main():
    load_dotenv()
    print("Starting ArXiv Paper Summarizer...")
    config = load_and_validate_config()
    
    # Extract config values
    categories = config["arxiv"]["categories"]
    keywords = config["arxiv"]["keywords"]
    max_results = config["arxiv"]["max_results"]
    
    github_config = config["github"]
    repo = github_config["repository"]
    usernames = github_config.get("usernames", [])
    issue_label = github_config.get("issue_label", "arxiv-summary")
    
    filter_model = config["models"]["filter"]
    summarize_model = config["models"]["summarize"]
    
    # 0. Determine start date
    last_run = get_last_issue_date(repo, issue_label)
    if last_run:
        print(f"Last run found: {last_run}")
        start_date = last_run
    else:
        print("No previous run found. Fetching latest papers (no date limit).")
        start_date = None
    end_date = datetime.now()

    # 1. Fetch
    print("--- Step 1: Fetching Papers ---")
    papers = fetch_arxiv_papers(categories, max_results, since_date=start_date)
    if not papers:
        print("No new papers found.")
        return

    # 2. Filter (LLM)
    print("--- Step 2: Filtering Papers ---")
    relevant_papers = filter_papers_with_llm(papers, keywords, filter_model)
    if not relevant_papers:
        print("No relevant papers found after filtering.")
        return

    # 3. Summarize
    print("--- Step 3: Summarizing Papers ---")
    summarized_papers = summarize_papers(relevant_papers, summarize_model)

    # 4. Create Issue
    print("--- Step 4: Creating GitHub Issue ---")
    create_issue(summarized_papers, repo, usernames, issue_label, start_date, end_date)
    
    print("Done!")

if __name__ == "__main__":
    main()
