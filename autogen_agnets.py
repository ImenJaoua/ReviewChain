# agents_autogen.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
import autogen
from chat_env import ChatEnv, ChatEnvConfig
from comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref,
)

from comment_judgement_prompt import (
    judgment_system_prompt,
    judgment_template,
)

import logging

from llm_config import (
    llm_config_reviewer,
    llm_config_developer,
    llm_config_comment_judge,
)


logging.getLogger("autogen").setLevel(logging.WARNING)


# HF LLM Wrapper
def local_hf_pipeline(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.float16
    ).eval()

    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

    def _generate(prompt, max_new_tokens=256):
        response = generator(prompt, max_new_tokens=max_new_tokens, return_full_text=False)
        return response[0]["generated_text"]

    return _generate

# Define Agents
reviewer_model = local_hf_pipeline("trained_model_A1")
developer_model = local_hf_pipeline("deepseek-ai/deepseek-coder-6.7b-instruct")
comment_judge_model = local_hf_pipeline("deepseek-ai/deepseek-coder-6.7b-instruct")

# Agent initialization
reviewer = autogen.AssistantAgent(
    name="Reviewer",
    system_message=review_classification_system_prompt,
    llm_config=llm_config_reviewer
)

developer = autogen.AssistantAgent(
    name="Developer",
    system_message=review_classification_system_prompt_ref,
    llm_config=llm_config_developer
)

comment_judge = autogen.AssistantAgent(
    name= "CommentJudge",
    system_message=judgment_system_prompt,
    llm_config=llm_config_comment_judge
)


def run_review_session(initial_code, max_rounds=3, reviewer_max_tokens=512, developer_max_tokens=512, old_code=""):

    config = ChatEnvConfig(with_memory=True, test_enabled=True)
    chat_env = ChatEnv(config, initial_code)
    print("\n=== Starting AutoGen Multi-Agent Code Review ===")

    for round_id in range(max_rounds):
        print(f"\n--- ROUND {round_id+1} ---")

        # Step 1: Reviewer review
        reviewer_prompt = review_classification_template.format(code_diff=chat_env.get("code"))
        review_comment = reviewer_model(reviewer_prompt, max_new_tokens=reviewer_max_tokens)
        chat_env.update("comments", review_comment)
        chat_env.append_history("Reviewer", review_comment)
        print("\n Reviewer:\n", review_comment)

        # Step 2: Developer refinement
        developer_prompt = review_classification_template_ref.format(
            code_diff=initial_code.strip(),
            review_comment=review_comment.strip(),
            old_file=old_code.strip()
        )
        refined_code = developer_model(developer_prompt, max_new_tokens=developer_max_tokens)
        chat_env.update_code(refined_code)
        chat_env.append_history("Developer", refined_code)
        print("\n Developer:\n", refined_code)

        # Step 3: Comment Judge
        comment_judge_prompt = judgment_template.format(
            code_review_comment=review_comment.strip(),
            initial_code=initial_code,
            code_changes=refined_code.strip()
        )
        judgment = comment_judge_model(comment_judge_prompt, max_new_tokens=512)
        chat_env.update("judgment", judgment)
        chat_env.append_history("CommentJudge", judgment)
        print("\n Comment Judge:\n", judgment)

        # Reinitialize reviewer prompt based on judgment

        reviewer_prompt = judgment.format(code=initial_code.strip())

    print("\n Final Refined Code:\n", chat_env.get_code())
    return chat_env.get_code()


if __name__ == "__main__":

    initial_code = """ @@ -595,8 +595,10 @@ namespace Kratos
             array_1d<double, 3> b = ZeroVector(3);
             b[0] = 1.0;
 
-            const array_1d<double, 3>  c = MathUtils<double>::CrossProduct(a, b);
-            const array_1d<double, 3>  d = MathUtils<double>::UnitCrossProduct(a, b);
+            array_1d<double, 3>  c, d;
+
+            MathUtils<double>::CrossProduct(c, b, a);
+            MathUtils<double>::UnitCrossProduct(d, b, a);
             
             KRATOS_CHECK_EQUAL(c[2], 2.0);
             KRATOS_CHECK_EQUAL(d[2], 1.0);
"""
    run_review_session(initial_code)
