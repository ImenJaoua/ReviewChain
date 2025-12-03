review_classification_system_prompt2 = """You are an expert in coding and peer-reviewing. Your role is the Comment Generator.

"""

review_classification_prompt2 = """### Code Review Comment Regeneration

You previously generated a review comment that was applied to the code change, but the resulting version of code was rejected by the Quality Estimator.

Your role now is to generate an improved review comment and guides the developer toward an acceptable version of code change.

Given:
1. The initial given **code change**(before refinment).
2. Your **previous review comment**.
3. The **justification from the quality estimator** explaining why the code change was rejected.

Generate an improved review comment. 

### Requirements:
- Be **specific, constructive, and concise** (avoid repeating generic advice).
- The justifictaion given by the Quality Estimator is only for your understanding; do not include it in your comment.
- If the previous review was partially correct, refine it rather than discarding it.
- The new comment should help the developer produce a version that would likely be **accepted in the next evaluation**.

### Input:
**Initial Code Change (before refinment):**
{code_diff}

**Your Previous Review Comment:**
{previous_comment}

**Quality Estimator Justification:**
{justification}

### Output Format:
Provide your response as a single, well-written review comment.
"""
