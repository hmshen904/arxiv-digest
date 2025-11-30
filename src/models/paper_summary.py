from dataclasses import dataclass
import json


@dataclass
class PaperSummary:
    """Structured summary of a research paper."""
    problem: str
    proposed_method: str
    key_results: str

    JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "problem": {
                "type": "string",
                "description": "The problem being addressed by the research paper"
            },
            "proposed_method": {
                "type": "string",
                "description": "The method or approach proposed to solve the problem"
            },
            "key_results": {
                "type": "string",
                "description": "The key results and findings of the research"
            }
        },
        "required": ["problem", "proposed_method", "key_results"],
        "additionalProperties": False
    }

    @classmethod
    def from_json(cls, json_str: str) -> "PaperSummary":
        """Parse a JSON string into a PaperSummary."""
        data = json.loads(json_str)
        return cls(
            problem=data["problem"],
            proposed_method=data["proposed_method"],
            key_results=data["key_results"]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "PaperSummary":
        """Create a PaperSummary from a dictionary."""
        return cls(
            problem=data["problem"],
            proposed_method=data["proposed_method"],
            key_results=data["key_results"]
        )

    @classmethod
    def error(cls, error_msg: str) -> "PaperSummary":
        """Create an error summary."""
        return cls(
            problem=f"Error: {error_msg}",
            proposed_method="N/A",
            key_results="N/A"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "problem": self.problem,
            "proposed_method": self.proposed_method,
            "key_results": self.key_results
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Format as markdown for display."""
        return (
            f"**Problem:** {self.problem}\n\n"
            f"**Proposed Method:** {self.proposed_method}\n\n"
            f"**Key Results:** {self.key_results}"
        )

    @classmethod
    def get_response_format(cls) -> dict:
        """Get the response format for LLM API calls."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "paper_summary",
                "strict": True,
                "schema": cls.JSON_SCHEMA
            }
        }
