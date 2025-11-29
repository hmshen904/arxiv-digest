# ArXiv Paper Summarizer

A GitHub Actions workflow that fetches recent ArXiv papers, filters them using LLMs (GitHub Models), summarizes them, and publishes the results as GitHub Issues.

## Features
- **Smart Filtering**: Uses LLMs (e.g., GPT-5-mini) to score paper relevance (0-10) based on your keywords.
- **Concise Summaries**: Generates high-quality summaries using capable models (e.g., GPT-5).
- **Incremental Fetching**: Only fetches papers published since the last run to avoid duplicates.
- **Zero Config Auth**: Uses `GITHUB_TOKEN` for all authentication (Models & Issues).
- **Daily Schedule**: Runs automatically every day at 08:00 UTC.

## Configuration

Edit `config.yaml` to customize your preferences:

```yaml
arxiv:
  categories:
    - "cs.AI"
    - "cs.LG"
  keywords:
    - "LLM"
    - "Agent"
  max_results: 20

github:
  usernames:
    - "your-username" # Users to tag in the issue
  issue_label: "arxiv-summary"

models:
  filter: "gpt-5-mini"
  summarize: "gpt-5"
```

## Local Development & Testing

You can run the tool locally without GitHub Actions.

### Prerequisites
1. Install [uv](https://github.com/astral-sh/uv) (or use pip).
2. A GitHub Personal Access Token (PAT) with `repo` scope (for creating issues) and access to GitHub Models.

### Setup
```bash
# Install dependencies
uv sync
```

### Running Locally
1. Create a `.env` file in the root directory:
   ```bash
   GITHUB_TOKEN=your_fine_grained_token
   GITHUB_REPOSITORY=owner/repo
   ```
2. Run the summarizer:
   ```bash
   uv run src/main.py
   ```

**Token Permissions (Fine-grained):**
- **Issues**: `Read and Write` (to create summaries and check last run).
- **Models**: `Read` (to access GitHub models.)

> [!NOTE]
> When running locally, the tool will try to create a real issue in the specified repository. If you just want to test the fetching/summarizing logic without creating an issue, you can modify `src/main.py` or `src/issue_creator.py` temporarily.

## GitHub Actions

The workflow is defined in `.github/workflows/summarize.yml`. It is configured to run:
- **Daily** at 08:00 UTC.
- **Manually** via the "Run workflow" button in the Actions tab.
