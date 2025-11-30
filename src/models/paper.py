from dataclasses import dataclass, field
from typing import Optional
from models.paper_summary import PaperSummary


@dataclass
class Paper:
    """Represents a research paper."""
    title: str
    link: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    published: Optional[str] = None
    summary: Optional[PaperSummary] = None
    pdf_url: Optional[str] = None

    @classmethod
    def from_arxiv_entry(cls, entry) -> "Paper":
        """Create a Paper from an arXiv feedparser entry."""
        link = entry.link
        return cls(
            title=entry.title.replace("\n", " "),
            link=link,
            abstract=entry.summary.replace("\n", " "),
            authors=[author.name for author in entry.authors],
            published=entry.published,
            pdf_url=link.replace("/abs/", "/pdf/") + ".pdf",
        )

    @classmethod
    def from_semantic_scholar(cls, data: dict) -> "Paper":
        """Create a Paper from Semantic Scholar API response."""
        open_access_pdf = data.get("openAccessPdf") or {}
        pdf_url = open_access_pdf.get("url") or None
        return cls(
            title=data.get("title", "").replace("\n", " "),
            link=data.get("url", ""),
            abstract=(data.get("abstract") or "").replace("\n", " "),
            authors=[a.get("name", "") for a in data.get("authors", [])],
            published=data.get("publicationDate"),
            pdf_url=pdf_url,
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
            summary=summary,
            pdf_url=data.get("pdf_url"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "link": self.link,
            "abstract": self.abstract,
            "authors": self.authors,
            "published": self.published,
            "summary": self.summary.to_dict() if self.summary else None,
            "pdf_url": self.pdf_url,
        }

    def get_pdf_url(self) -> Optional[str]:
        """Get PDF URL if available."""
        return self.pdf_url
