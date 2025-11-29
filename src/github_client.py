import os
import requests
from datetime import datetime


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token=None, repo=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN is required")
        if not self.repo:
            raise ValueError("GITHUB_REPOSITORY is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _url(self, endpoint):
        """Build API URL for the repo."""
        return f"{self.BASE_URL}/repos/{self.repo}/{endpoint}"
    
    def get_last_issue_date(self, issue_label="arxiv-summary"):
        """Get the creation date of the most recent issue with the given label."""
        url = self._url("issues")
        params = {
            "labels": issue_label,
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 1
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                issues = response.json()
                if issues:
                    created_at = issues[0]["created_at"]
                    return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"Error fetching last issue date: {e}")
        
        return None
    
    def create_issue(self, title, body, labels=None, assignees=None):
        """Create a new issue in the repository."""
        url = self._url("issues")
        data = {
            "title": title,
            "body": body,
        }
        
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        print(f"Creating issue '{title}' in {self.repo}...")
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 201:
            print(f"Issue created successfully: {response.json()['html_url']}")
            return response.json()
        else:
            print(f"Failed to create issue: {response.status_code} - {response.text}")
            return None
