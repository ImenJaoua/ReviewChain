review_classification_system_prompt_ref = """You are an expert in coding and code peer-reviewing."""

review_classification_template_ref = """
Given the following initial code change (diff format) and a review comment.Your task is to generate an updated version of the code that addresses the review feedback.

### Initial code changes:
{code_diff}

### Review comment:
{review_comment}

Return ONLY the refined code.
"""
