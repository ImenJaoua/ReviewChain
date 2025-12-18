quality_estimator_system_prompt = """You are a Quality Estimator for code review.
Your job is to analyze a code diff and decide if it requires a review comment.
"""

quality_estimator_template = """
Evaluate the quality of the following refined code and classify it as:

- rejected (1): The code change likely contains an issue and needs a review comment. 
- acceptable (0) : The code change appears acceptable and does NOT need a review comment.

### Refined Code:
{code_diff}

Respond with ONLY this JSON format (no ```json blocks, no markdown):
{{"decision": <0 or 1>, "justification": "your reason here"}}
"""
