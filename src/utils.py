from pathlib import Path
from datetime import datetime


def get_tmp_dir(subdir: str) -> Path:
    """Get the tmp directory path for a given subdirectory."""
    tmp_dir = Path(__file__).parent.parent / "tmp" / subdir
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def get_timestamp() -> str:
    """Get current timestamp in a filename-safe format."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Create a safe filename from a string."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name[:max_length])


def save_to_tmp(subdir: str, filename: str, content: str) -> Path:
    """
    Save content to a file in the tmp directory.
    
    Args:
        subdir: Subdirectory within tmp (e.g., 'summaries', 'issues')
        filename: Name of the file to create
        content: Content to write to the file
    
    Returns:
        Path to the saved file
    """
    tmp_dir = get_tmp_dir(subdir)
    filepath = tmp_dir / filename
    
    with open(filepath, "w") as f:
        f.write(content)
    
    return filepath


def save_summary_to_tmp(paper: dict, summary_text: str) -> Path:
    """Save individual paper summary to tmp folder for inspection."""
    safe_title = sanitize_filename(paper['title'])
    timestamp = get_timestamp()
    filename = f"{timestamp}_{safe_title}.md"
    
    content = f"# {paper['title']}\n\n"
    content += f"**Authors:** {', '.join(paper['authors'])}\n\n"
    content += f"**Abstract:** {paper['abstract']}\n\n"
    content += "---\n\n"
    content += "## LLM Summary\n\n"
    content += summary_text
    
    return save_to_tmp("summaries", filename, content)


def save_issue_to_tmp(title: str, body: str) -> Path:
    """Save the issue content to tmp folder before posting to GitHub."""
    timestamp = get_timestamp()
    filename = f"{timestamp}_issue.md"
    
    content = f"# {title}\n\n{body}"
    
    filepath = save_to_tmp("issues", filename, content)
    print(f"Issue saved to: {filepath}")
    return filepath
