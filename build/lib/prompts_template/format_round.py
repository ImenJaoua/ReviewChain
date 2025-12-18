review_format_system_prompt = """You are an expert in coding and code peer-reviewing. Your role is the Comment Generator."""


review_format_prompt = """
You generated a comment for a code change, but the comment was rejected by the Format Judge.
Your role now is to correct the comment to meet the Format Judge's requirements.

A review comment should highlight the main issues, improvements, or suggestions for the code changes.
The generated review comment should be concise, relevant, clear, useful, and complete.

Here is the format judge's feedback:
{justification}

Here is your previous rejected comment:
{previous_comments}

Correct the comment based on the same code diff below:
{code_diff}
"""
