from dataclasses import dataclass, field
from typing import Optional
from models.paper_summary import PaperSummary


@dataclass
class Paper:
    """Represents an arXiv paper."""
    title: str
    link: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    published: Optional[str] = None
    summary: Optional[PaperSummary] = None

    @classmethod
    def from_arxiv_entry(cls, entry) -> "Paper":
        """Create a Paper from an arXiv feedparser entry."""
        return cls(
            title=entry.title.replace("\n", " "),
            link=entry.link,
            abstract=entry.summary.replace("\n", " "),
            authors=[author.name for author in entry.authors],
            published=entry.published
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        """Create a Paper from a dictionary."""
        summary = data.get("llm_summary") or data.get("summary")
        if isinstance(summary, dict):
            summary = PaperSummary.from_dict(summary)
        return cls(
            title=data["title"],
            link=data["link"],
            abstract=data.get("abstract", ""),
            authors=data.get("authors", []),
            published=data.get("published"),
            summary=summary
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "link": self.link,
            "abstract": self.abstract,
            "authors": self.authors,
            "published": self.published,
            "summary": self.summary.to_dict() if self.summary else None
        }

    def get_pdf_url(self) -> str:
        """Convert arXiv abstract URL to PDF URL."""
        return self.link.replace("/abs/", "/pdf/") + ".pdf"
