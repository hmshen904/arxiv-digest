import os
import requests
from datetime import datetime
from utils import save_issue_to_tmp


def get_last_issue_date(repo, issue_label="arxiv-summary"):
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token or not repo:
        return None

    label = issue_label
    
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "labels": label,
        "state": "all", # Check closed issues too
        "sort": "created",
        "direction": "desc",
        "per_page": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            issues = response.json()
            if issues:
                # Return datetime object
                created_at = issues[0]["created_at"]
                return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Error fetching last issue date: {e}")
        
    return None

def create_issue(summaries, repo, usernames=None, issue_label="arxiv-summary", start_date=None, end_date=None):
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token or not repo:
        print("Warning: GITHUB_TOKEN or repository not set. Skipping issue creation.")
        return

    if usernames is None:
        usernames = []
    label = issue_label

    # Format Issue Title with time range
    date_str = datetime.now().strftime("%Y-%m-%d")
    if start_date and end_date:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        title = f"ArXiv Summary - {date_str} (papers from {start_str} to {end_str})"
    else:
        title = f"ArXiv Summary - {date_str}"
    
    body = f"# ArXiv Paper Summaries ({date_str})\n\n"
    body += f"Found {len(summaries)} relevant papers.\n\n"
    
    for paper in summaries:
        body += f"## {paper['title']}\n"
        body += f"**Authors:** {', '.join(paper['authors'])}\n\n"
        body += f"[View on ArXiv]({paper['link']})\n\n"
        body += f"### Summary\n{paper['llm_summary']}\n\n"
        body += "---\n\n"

    # Save issue to tmp folder before posting
    save_issue_to_tmp(title, body)

    # Create Issue via API
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "labels": [label]
    }
    
    # Assign users to the issue
    if usernames:
        data["assignees"] = usernames
    
    print(f"Creating issue '{title}' in {repo}...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Issue created successfully: {response.json()['html_url']}")
    else:
        print(f"Failed to create issue: {response.status_code} - {response.text}")

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    repo = config.get("github", {}).get("repository")
    usernames = config.get("github", {}).get("usernames", [])
    issue_label = config.get("github", {}).get("issue_label", "arxiv-summary")
    
    # Test with dummy data (will fail locally without correct env vars)
    dummy_summaries = [{
        "title": "Test Paper",
        "authors": ["Me", "You"],
        "link": "http://arxiv.org/abs/1234.5678",
        "llm_summary": "This is a summary."
    }]
    create_issue(dummy_summaries, repo, usernames, issue_label)
