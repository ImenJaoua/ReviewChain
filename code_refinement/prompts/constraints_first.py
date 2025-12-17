prompt_constraints = """
CRITICAL RULES:
- NO markdown code blocks
- NO explanations or text
- NO partial code or placeholders
- NO changes beyond the review comment
- NO adding features, refactoring, or style changes

TASK:
Apply this review comment to the code change below.
Return the complete corrected code change immediately.

Code Change:
{code_diff}

Review Comment:
{review_comment}
"""