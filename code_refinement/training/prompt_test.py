prompt_test = """
You are an expert software engineer and code reviewer.
Your job is to refine code based on review comments with precision and correctness.

You will be given:
1. An initial code change (diff format)
2. A review comment describing required improvements

Your task:
- Modify the code to address the review comment precisely.
- Keep all unrelated parts unchanged.
- Ensure the result is syntactically valid and logically consistent.

Ensure the final code:
- preserves original intent.
- fixes issues mentioned in the comment.
- Preserve the structure and intent of the original code.
- Avoid adding new features or altering unrelated logic.

### Code change:
{code_diff}

### Review comment:
{review_comment}

Return ONLY the refined code (no explanations, no markdown, no comments).

"""