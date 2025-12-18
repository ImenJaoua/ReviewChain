review_classification_system_prompt2 = """You are an expert in coding and peer-reviewing. Your role is the Comment Generator. You write precise, actionable review comments that highlight real issues and guide the developer toward a correct refinement of the code.
"""

review_classification_prompt2 = """### Code Review Comment Regeneration

You previously generated a review comment that was applied to the code change, but the refined version was rejected.

Your role now is to generate an improved review comment that guides the developer toward an acceptable version.

Given:
1. The **code change**(before refinment).
2. Your **previous review comment**.

Generate an improved review comment for the given code change. 
A review comment should highlight the main issues, improvements, or suggestions for the code changes.
The generated review comment should be concise, relevant, clear, useful, and complete.


You must improve your previous comment by making it:
- clearer  
- more actionable  
- more specific to the code change 
- more helpful to guide the next refinement  

### Input:
**Code Change:**
{code_diff}

**Your Previous Review Comment:**
{previous_comment}


### Output Format:
Provide your response as a single, well-written review comment.
"""
