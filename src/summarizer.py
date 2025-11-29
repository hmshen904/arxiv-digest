import os
from openai import OpenAI

from paper_summary import PaperSummary
from utils import save_summary_to_tmp


def summarize_papers(papers, model_name):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

    summaries = []
    print(f"Summarizing {len(papers)} papers...")

    for paper in papers:
        print(f"  Summarizing: {paper['title']}")
        prompt = f"""Summarize this research paper by extracting the following information.
Return a JSON object with exactly these fields:
- "problem": What problem is being addressed?
- "proposed_method": What approach or method is proposed?
- "key_results": What are the main findings and results?

Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Abstract: {paper['abstract']}"""

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
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    summarize_model = config.get("models", {}).get("summarize", "gpt-4o")
    
    # Test with dummy data
    dummy_papers = [{
        "title": "Test Paper",
        "authors": ["Author A", "Author B"],
        "abstract": "This is a test abstract about LLMs and agents."
    }]
    try:
        summarized = summarize_papers(dummy_papers, summarize_model)
        print(summarized[0]['llm_summary'])
    except Exception as e:
        print(f"Test failed: {e}")
