prompt_steps = """
You are refining code based on a review comment.

Code Change:
{code_diff}

Review Comment:
{review_comment}

Execute these steps:
STEP 1: Identify the exact lines that need modification
STEP 2: Determine the minimal code change required
STEP 3: Apply the change while preserving all other code
STEP 4: Verify syntax and logic correctness

Output ONLY the final revised code change (no steps, no markdown, no commentary).
"""