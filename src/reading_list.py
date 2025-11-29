import os
import re
import json
from github_client import GitHubClient

READING_LIST_LABEL = "reading-list"
READING_LIST_TITLE = "📚 ArXiv Reading List"


def parse_papers(body: str) -> dict:
    """Parse papers with Read Later checkboxes from issue body."""
    # Matches: ## Title ... [View on ArXiv](url) ... - [x] 📚 Read Later
    pattern = r"## ([^\n]+)\n[\s\S]*?\[View on ArXiv\]\(([^)]+)\)[\s\S]*?- \[([ x])\] 📚 Read Later"
    papers = {}
    for match in re.finditer(pattern, body):
        title = match.group(1).strip()
        url = match.group(2)
        checked = match.group(3) == "x"
        papers[title] = {"url": url, "checked": checked}
    return papers


def find_newly_checked(old_body: str, new_body: str) -> list:
    """Find papers that were newly checked."""
    old_papers = parse_papers(old_body)
    new_papers = parse_papers(new_body)
    
    newly_checked = []
    for title, data in new_papers.items():
        old_data = old_papers.get(title)
        if data["checked"] and (not old_data or not old_data["checked"]):
            newly_checked.append({"title": title, "url": data["url"]})
    return newly_checked


class ReadingListClient(GitHubClient):
    """Extended GitHub client for reading list management."""
    
    def get_reading_list_issue(self):
        """Find the open reading list issue, if it exists."""
        url = self._url("issues")
        params = {
            "labels": READING_LIST_LABEL,
            "state": "open",
            "per_page": 1
        }
        import requests
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            issues = response.json()
            if issues:
                return issues[0] # Only 1 reading list issue per repository
        return None
    
    def create_reading_list_issue(self):
        """Create a new reading list issue."""
        return self.create_issue(
            title=READING_LIST_TITLE,
            body="# Papers to Read\n\nPapers marked for later reading from ArXiv digests.\n\n---\n\n",
            labels=[READING_LIST_LABEL]
        )
    
    def update_issue_body(self, issue_number: int, body: str):
        """Update an issue's body."""
        import requests
        url = self._url(f"issues/{issue_number}")
        response = requests.patch(url, headers=self.headers, json={"body": body})
        if response.status_code != 200:
            raise RuntimeError(f"Failed to update issue: {response.status_code} - {response.text}")
        return response.json()
    
    def add_to_reading_list(self, papers: list, source_issue_number: int):
        """Add papers to the reading list issue."""
        if not papers:
            print("No papers to add")
            return
        
        # Find or create reading list issue
        reading_list = self.get_reading_list_issue()
        if not reading_list:
            reading_list = self.create_reading_list_issue()
            print(f"Created new reading list issue: #{reading_list['number']}")
        
        # Append papers
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        body = reading_list["body"] or ""
        
        for paper in papers:
            entry = f"- [ ] [{paper['title']}]({paper['url']}) *(added {today} from #{source_issue_number})*\n"
            body += entry
            print(f"Adding: {paper['title']}")
        
        self.update_issue_body(reading_list["number"], body)
        print(f"Updated reading list issue #{reading_list['number']}")


def main():
    """Process issue edit event from GitHub Actions."""
    # Read event payload
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH not set")
    
    with open(event_path) as f:
        event = json.load(f)
    
    issue = event.get("issue", {})
    changes = event.get("changes", {})
    
    # Check if body was changed
    if "body" not in changes:
        print("No body changes detected")
        return
    
    old_body = changes["body"].get("from", "")
    new_body = issue.get("body", "")
    
    # Find newly checked papers
    newly_checked = find_newly_checked(old_body, new_body)
    if not newly_checked:
        print("No newly checked Read Later boxes")
        return
    
    print(f"Found {len(newly_checked)} newly checked papers")
    
    # Add to reading list
    client = ReadingListClient()
    client.add_to_reading_list(newly_checked, issue["number"])


if __name__ == "__main__":
    main()
