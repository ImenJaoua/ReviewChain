review_classification_system_prompt_ref = """
You are an expert software engineer and code reviewer.
Respond ONLY with the revised code change.
"""

review_classification_template_ref = """
### Task: Code Change Refinement
Given the following code changes and a review comment, generate the revised code change.
Your output must contain ONLY the updated code change.
Do NOT add explanations, descriptions, or commentary.

### Input:
**Original Code Change:**
{code_diff}

**Review Comment:**
{review_comment}
"""




