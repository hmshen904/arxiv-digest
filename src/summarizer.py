from paper_summary import PaperSummary
from utils import save_summary_to_tmp, extract_text_from_pdf, call_with_retry


def get_pdf_url(arxiv_link):
    """Convert ArXiv abstract URL to PDF URL."""
    # https://arxiv.org/abs/2401.12345 -> https://arxiv.org/pdf/2401.12345.pdf
    return arxiv_link.replace("/abs/", "/pdf/") + ".pdf"


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
        
        # Use full text if available, otherwise fall back to abstract
        if full_text:
            content_section = f"Full Paper Text:\n{full_text}"
            print("    Using full paper text for summarization")
        else:
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
            response = call_with_retry(lambda: client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert researcher assistant. Provide concise and insightful summaries."},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                response_format=PaperSummary.get_response_format()
            ))
            
            summary = PaperSummary.from_json(response.choices[0].message.content)
            paper['llm_summary'] = summary
            
            # Save to tmp folder for inspection (local only)
            save_summary_to_tmp(paper, summary.to_json())
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
    from openai import OpenAI
    from dotenv import load_dotenv
    from utils import load_config
    
    load_dotenv()
    config = load_config()
    
    summarize_model = config["models"]["summarize"]
    base_url = config["llm_service"]["base_url"]
    
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
