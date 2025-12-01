review_classification_system_prompt = """You are an expert in coding and code peer-reviewing."""

review_classification_template = """###
You are supposed to generate a review comment that you
consider perfect for the given code changes
for a given Code changes hunk.

The generated review comment should highlight the main issues,
improvements, or suggestions while considering conciseness,
relevancy, clarity, usefulness, and completeness.

think step by step to ensure all important aspects are covered.

Here is an example for comment generation:

input Code changes:
   @@ -273,6 +273,10 @@ class RootPathHandler(BaseTaskHistoryHandler):
        def get(self):
            self.redirect("/static/visualiser/index.html")
    
   +    def head(self):

Generated comment:

  Is the name "head" a convention for health checking? Regardless it caught me by surprise, maybe add some docs to this function on why it exist? It should also say what 204.


### Code changes:
{code_diff}
"""