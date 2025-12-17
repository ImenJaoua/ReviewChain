prompt_cot = """
You are an expert software engineer refining code based on review feedback.

## Input
Code Change:
{code_diff}

Review Comment:
{review_comment}

## Process
First, analyze the review in <thinking> tags:
<thinking>
1. What specific issues are mentioned?
2. Which lines of code need modification?
3. What is the minimal change required?
4. Are there any edge cases to consider?
</thinking>

Then output the refined code change with NO additional text, markdown, or explanations.
"""