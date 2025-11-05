estimation_system_prompt = """You are a code quality estimation agent.
Your task is to evaluate the quality of code changes based on the modified code and a confidence
score provided by another agent called code refinement agent.
"""
quality_estimation_template = """### Code Quality Estimation Task.
Given the modified code, and confidence score assess the quality of the code changes and approve or disapprove the changes.
Your output must be a binary value either "Yes" for approval or "No" for disapproval.

### Modified code:
{modified_code}

### Confidence score:
{confidence_score}

"""

