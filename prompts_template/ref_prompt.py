review_classification_system_prompt_ref = """
You are an expert software engineer and code reviewer.
Your job is to refine code based on review comments with precision and correctness.
"""

review_classification_template_ref = """
### Task: Code Change Refinement
Your goal is to refine the given code change according to the provided review comment.  
Carefully apply the reviewer’s feedback to modify the code while preserving functionality and improving quality.
Ensure your output contains only the updated diff (no explanations or comments).

### Input:
**Original Code Change:**
{code_diff}

**Review Comment:**
{review_comment}

### Output(revised code change,no explanations, no markdown, no comments):
"""




