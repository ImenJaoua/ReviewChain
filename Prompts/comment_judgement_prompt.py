judgment_system_prompt = """You are responsible for judging
the quality of generated code review comments."""

judgment_template = """### Code review comment quality judgment.
Given the initial code, modified code, and a generated review comment,
judge the quality of the review comment based on its relevance,
clarity, usefulness, civilization, content and completeness.
civilization means the comment should be polite and respectful.
content means level of descriptivity and prescriptivity of the comment.

return a well structured comment generation prompt for comment generator LLM.


### Code review comment:
{code_review_comment}

### Initial code:
{initial_code}

###  Code changes:
{code_changes}
"""