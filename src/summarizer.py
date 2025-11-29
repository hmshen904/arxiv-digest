import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from utils import save_summary_to_tmp


def summarize_papers(papers, model_name):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")

    endpoint = "https://models.inference.ai.azure.com"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    summaries = []
    print(f"Summarizing {len(papers)} papers...")

    for paper in papers:
        print(f"  Summarizing: {paper['title']}")
        prompt = f"""
        Please provide a concise and insightful summary of the following research paper.
        Focus on the problem being solved, the proposed method, and the key results.
        Format the output in Markdown.

        Title: {paper['title']}
        Authors: {', '.join(paper['authors'])}
        Abstract: {paper['abstract']}
        """

        try:
            response = client.complete(
                messages=[
                    SystemMessage(content="You are an expert researcher assistant."),
                    UserMessage(content=prompt),
                ],
                model=model_name            )
            
            summary_text = response.choices[0].message.content
            paper['llm_summary'] = summary_text
            
            # Save to tmp folder for inspection
            saved_path = save_summary_to_tmp(paper, summary_text)
            print(f"    Saved summary to: {saved_path}")
            
            summaries.append(paper)
            
        except Exception as e:
            print(f"Error summarizing paper '{paper['title']}': {e}")
            error_msg = f"Error generating summary: {e}"
            paper['llm_summary'] = error_msg
            
            # Save error to tmp folder too
            save_summary_to_tmp(paper, error_msg)
            
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
