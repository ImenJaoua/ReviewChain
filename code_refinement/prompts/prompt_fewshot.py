fewshot_prompt = """You are an expert software engineer and code reviewer.

## Task: Code Change Refinement
Your goal is to refine the given code change according to the provided review comment.  
Carefully apply the reviewer’s feedback to modify the code while preserving functionality and improving quality.
Ensure your output contains only the updated diff (no explanations or comments).

## Example1: 

### Input Code Change:
@@ -273,6 +273,10 @@ class RootPathHandler(BaseTaskHistoryHandler):
     def get(self):
         self.redirect("/static/visualiser/index.html")
 
+    def head(self):
       
### Review Comment:
Is the name "head" a convention for health checking? Regardless it caught me by surprise, maybe add some docs to this function on why it exist? It should also say what 204.

### Expected Output:
@@ -274,6 +274,7 @@ class RootPathHandler(BaseTaskHistoryHandler):
         self.redirect("/static/visualiser/index.html")
 
     def head(self):
+        \"\"\"HEAD endpoint for health checking the scheduler\"\"\"
         self.set_status(204)
         self.finish()

## Example 2:

### Input Code Change:
@@ -423,6 +423,14 @@ def handle_ext_handler(self, ext_handler, etag):
 
         try:
             state = ext_handler.properties.state
+
+            self.get_artifact_error_state.reset()

### Review Comment:
the error state should be reset after the "if decide_version" (because download succeeded) now, since with this change we short-circuit the logic if there is not a new goal state, it seems to me that the error state is not needed and we should always report errors (since it is a new goal state) -- could you review the code to check if this is true?

### Expected Output:
@@ -424,7 +424,6 @@ class ExtHandlersHandler(object):
         try:
             state = ext_handler.properties.state
 
-            self.get_artifact_error_state.reset()
             if self.last_etag == etag:
                 if self.log_etag:
                     ext_handler_i.logger.verbose("Incarnation 0 did not change, not processing GoalState", etag)



## Input:
**Original Code Change:**
{code_diff}

**Review Comment:**
{review_comment}

## Output(revised code change):
"""
