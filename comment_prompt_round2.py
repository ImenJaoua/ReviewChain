review_classification_template2 = """You are an expert in coding and code peer-reviewing."""

review_classification_system_prompt2 = """### Code Review Comment Regeneration

In the previous review round:
- You analyzed a code change and generated a review comment.
- Your comment was applied to the code, producing a revised version.
- However, the revised code was **rejected by the quality estimator** due to remaining issues.

You will now conduct a **new-round review**.

### Your Task:
Given:
1. The latest **code change** after your previous review comment.
2. Your **previous review comment**.
3. The **justification from the quality estimator** explaining why the code was rejected.

Generate an improved, non-redundant review comment.

### Requirements:
- Focus on issues that remain unresolved or newly introduced.
- Be **specific, constructive, and concise** (avoid repeating generic advice).
- If the previous review was partially correct, refine it rather than discarding it.
- The new comment should help the developer produce a version that would likely be **accepted in the next evaluation**.

### Input:
**Code Change:**
{code_diff}

**Previous Review Comment:**
{previous_comment}

**Quality Estimator Justification:**
{justification}

### Output Format:
Provide your response as a single, well-written review comment.
"""
