from datetime import datetime
from paper_summary import PaperSummary
from utils import save_issue_to_tmp


def format_summary(summary):
    """Format a summary into markdown."""
    if isinstance(summary, PaperSummary):
        return summary.to_markdown()
    return str(summary)


def create_issue(github_client, summaries, usernames=None, issue_label="arxiv-summary", start_date=None, end_date=None):
    if usernames is None:
        usernames = []

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
        body += f"### Summary\n{format_summary(paper['llm_summary'])}\n\n"
        body += f"[View on ArXiv]({paper['link']})\n\n"
        body += "---\n\n"

    # Save issue to tmp folder before posting
    save_issue_to_tmp(title, body)

    # Create Issue via API
    github_client.create_issue(
        title=title,
        body=body,
        labels=[issue_label],
        assignees=usernames if usernames else None
    )


if __name__ == "__main__":
    from github_client import GitHubClient
    from utils import load_config
    
    config = load_config()
    
    usernames = config.get("github", {}).get("usernames", [])
    issue_label = config.get("github", {}).get("issue_label", "arxiv-summary")
    
    # Test with dummy data (will fail locally without correct env vars)
    try:
        client = GitHubClient()
        dummy_summaries = [{
            "title": "Test Paper",
            "authors": ["Me", "You"],
            "link": "http://arxiv.org/abs/1234.5678",
            "llm_summary": "This is a summary."
        }]
        create_issue(client, dummy_summaries, usernames, issue_label)
    except ValueError as e:
        print(f"Test skipped: {e}")
