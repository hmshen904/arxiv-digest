import json
from models import Paper
from utils import call_with_retry


RELEVANCE_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "description": "Relevance score from 0-10"
        }
    },
    "required": ["score"],
    "additionalProperties": False
}


def filter_papers_with_llm(papers: list[Paper], keywords, model_name, client) -> list[Paper]:
    """Filter papers by relevance using an LLM.
    
    Args:
        papers: List of papers to filter.
        keywords: List of keywords representing user interests.
        model_name: Name of the LLM model to use.
        client: OpenAI-compatible client.
    
    Returns:
        List of papers with relevance score >= 7.
    """
    filtered_papers = []
    
    print(f"Filtering {len(papers)} papers with LLM...")

    for idx, paper in enumerate(papers):
        prompt = f"""Rate the relevance of this paper to the user's interests.

User's interests: {', '.join(keywords)}

The paper is considered relevant if it aligns with ANY of the interests listed above (not necessarily all of them).

Paper Title: {paper.title}
Abstract: {paper.abstract}

Return a score from 0-10 where 0 = not relevant, 10 = highly relevant."""

        try:
            response = call_with_retry(lambda: client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a research assistant that helps filter academic papers based on user interests."},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "relevance_score",
                        "strict": True,
                        "schema": RELEVANCE_SCORE_SCHEMA
                    }
                }
            ))
            
            result = json.loads(response.choices[0].message.content)
            score = result["score"]
            
            if score >= 7:
                print(f"  [KEEP] ({idx + 1}/{len(papers)}) {paper.title} (Score: {score})")
                filtered_papers.append(paper)
            else:
                print(f"  [SKIP] ({idx + 1}/{len(papers)}) {paper.title} (Score: {score})")
                
        except Exception as e:
            print(f"Error filtering paper '{paper.title}': {e}")
            # On error, keep it to be safe
            filtered_papers.append(paper)
        
    print(f"Selected {len(filtered_papers)} relevant papers using {model_name}.")
    return filtered_papers
