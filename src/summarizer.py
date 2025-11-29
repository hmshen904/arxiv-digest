import tempfile
import requests
import fitz  # PyMuPDF

from paper_summary import PaperSummary
from utils import save_summary_to_tmp


def get_pdf_url(arxiv_link):
    """Convert ArXiv abstract URL to PDF URL."""
    # https://arxiv.org/abs/2401.12345 -> https://arxiv.org/pdf/2401.12345.pdf
    return arxiv_link.replace("/abs/", "/pdf/") + ".pdf"


def extract_text_from_pdf(pdf_url, max_chars=50000):
    """Download PDF and extract text content."""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            
            doc = fitz.open(tmp_file.name)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Truncate to avoid token limits
            if len(text) > max_chars:
                text = text[:max_chars] + "\n... [truncated]"
            
            return text
    except Exception as e:
        print(f"    Warning: Could not extract PDF text: {e}")
        return None


def summarize_papers(papers, model_name, client):
    summaries = []
    print(f"Summarizing {len(papers)} papers...")

    for paper in papers:
        print(f"  Summarizing: {paper['title']}")
        
        # Try to get full paper text from PDF
        full_text = None
        if 'link' in paper:
            pdf_url = get_pdf_url(paper['link'])
            print(f"    Fetching PDF: {pdf_url}")
            full_text = extract_text_from_pdf(pdf_url)
        
        # TODO: re-enable when fully tested
        # Use full text if available, otherwise fall back to abstract
        # if full_text:
        #     content_section = f"Full Paper Text:\n{full_text}"
        #     print("    Using full paper text for summarization")
        # else:
        content_section = f"Abstract: {paper['abstract']}"
        print("    Falling back to abstract for summarization")
        
        prompt = f"""Summarize this research paper by extracting the following information.
Return a JSON object with exactly these fields:
- "problem": What problem is being addressed?
- "proposed_method": What approach or method is proposed?
- "key_results": What are the main findings and results?

Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
{content_section}"""

        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert researcher assistant. Provide concise and insightful summaries."},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                response_format=PaperSummary.get_response_format()
            )
            
            summary = PaperSummary.from_json(response.choices[0].message.content)
            paper['llm_summary'] = summary
            
            # Save to tmp folder for inspection
            saved_path = save_summary_to_tmp(paper, summary.to_json())
            print(f"    Saved summary to: {saved_path}")
            
            summaries.append(paper)
            
        except Exception as e:
            print(f"Error summarizing paper '{paper['title']}': {e}")
            paper['llm_summary'] = PaperSummary.error(str(e))
            
            # Save error to tmp folder too
            save_summary_to_tmp(paper, paper['llm_summary'].to_json())
            
            summaries.append(paper)

    return summaries

if __name__ == "__main__":
    import os
    import yaml
    from openai import OpenAI
    from dotenv import load_dotenv
    
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    summarize_model = config.get("models", {}).get("summarize", "gpt-4o")
    base_url = config.get("llm_service", {}).get("base_url", "https://models.inference.ai.azure.com")
    
    client = OpenAI(base_url=base_url, api_key=os.environ.get("GITHUB_TOKEN"))
    
    # Test with dummy data
    dummy_papers = [{
        "title": "Test Paper",
        "authors": ["Author A", "Author B"],
        "abstract": "This is a test abstract about LLMs and agents.",
        "link": "https://arxiv.org/abs/2401.00001"
    }]
    try:
        summarized = summarize_papers(dummy_papers, summarize_model, client)
        print(summarized[0]['llm_summary'])
    except Exception as e:
        print(f"Test failed: {e}")
