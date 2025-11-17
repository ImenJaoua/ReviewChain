review_classification_system_prompt = """Act as an expert in coding and code peer-reviewing."""

review_classification_template = """### you are going to gnerate a code review comment for a professional code developer.
 the goal is to generate review comments for a given code change. 
 the comment should be explicit, civilized, and helpful enough to address the issues of the represented code.
precisely follow the instructions below:
1. Analyze the code changes provided in the "Code changes" section.
2. Identify any potential issues, improvements, or suggestions related to code quality, readability, performance, security, and best practices.
3. Generate a constructive and detailed review comment that addresses the identified points.
### Input:  
### Code changes:
{code_diff}
"""