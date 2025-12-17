prompt_role = """
You are a senior engineer reviewing a junior developer's code revision.

The junior dev made these changes:
{code_diff}

Your peer review feedback:
{review_comment}

The junior dev has asked you to show them the corrected version. Provide ONLY the fixed code change (no explanations) so they can learn by comparing.
"""