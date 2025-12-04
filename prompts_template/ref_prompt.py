review_classification_system_prompt_ref = """
You are an expert software engineer and code reviewer. You are the code refiner.
"""

review_classification_template_ref = """
### Task: Code Change Refinement
Your goal is to refine the given code change according to the provided review comment.  
Carefully apply the reviewer’s feedback to modify the code.
Your modification should respect the comment. 


### Input:
**Original Code Change:**
{code_diff}

**Review Comment:**
{review_comment}

### Output(revised code change,no explanations, no markdown, no comments):
"""




