# agents_autogen.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
import autogen
from typing import List, Dict, Any, Optional, Callable
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

from quality_estimation_prompt import (
    estimation_system_prompt,
    quality_estimation_template,
)

import logging

from llm_config import (
    llm_config_reviewer,
    llm_config_developer,
    llm_config_comment_judge,
    llm_config_quality_estimator,
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

class LocalHFModelClient:
    """Custom model client for local Hugging Face pipelines"""
    
    def __init__(self, pipeline, max_tokens=512):
        self.pipeline = pipeline
        self.max_tokens = max_tokens
    
    def __call__(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call pipeline and return response"""
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        response = self.pipeline(prompt, max_new_tokens=max_tokens)
        return response


# Define model pipelines
reviewer_pipeline = local_hf_pipeline("trained_model_A1")
developer_pipeline = local_hf_pipeline("deepseek-ai/deepseek-coder-6.7b-instruct")
comment_judge_pipeline = local_hf_pipeline("deepseek-ai/deepseek-coder-6.7b-instruct")
quality_estimator_pipeline = local_hf_pipeline("QE_model")

# Create custom clients
reviewer_client = LocalHFModelClient(reviewer_pipeline)
developer_client = LocalHFModelClient(developer_pipeline)
comment_judge_client = LocalHFModelClient(comment_judge_pipeline)
quality_estimator_client = LocalHFModelClient(quality_estimator_pipeline)

# Store clients in a dictionary for easy access
agent_clients = {}

# Agent initialization with required model_client
reviewer = AssistantAgent(
    name="Reviewer",
    model_client=reviewer_client,
    system_message=review_classification_system_prompt
)
agent_clients["Reviewer"] = reviewer_client

developer = AssistantAgent(
    name="Developer",
    model_client=developer_client,
    system_message=review_classification_system_prompt_ref
)
agent_clients["Developer"] = developer_client

comment_judge = AssistantAgent(
    name="CommentJudge",
    model_client=comment_judge_client,
    system_message=judgment_system_prompt
)
agent_clients["CommentJudge"] = comment_judge_client

quality_estimator = AssistantAgent(
    name="QualityEstimator",
    model_client=quality_estimator_client,
    system_message=estimation_system_prompt
)
agent_clients["QualityEstimator"] = quality_estimator_client

def get_agent_response(agent, prompt, max_tokens=512):
    """Get response from agent using the stored client"""
    client = agent_clients[agent.name]
    response = client(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response

def run_review_session(initial_code, max_rounds=3, reviewer_max_tokens=512, 
                       developer_max_tokens=512, old_code="",
                       message_callback: Optional[Callable[[str, str, int], None]] = None):
    """
    Run multi-agent code review session
    
    Args:
        initial_code: The code to review
        max_rounds: Number of review rounds
        reviewer_max_tokens: Max tokens for reviewer
        developer_max_tokens: Max tokens for developer
        old_code: Previous version of code (optional)
        message_callback: Callback function(agent_name, message, round_num) for UI updates
    
    Returns:
        Final refined code
    """
    config = ChatEnvConfig(with_memory=True, test_enabled=True)
    chat_env = ChatEnv(config, initial_code)
    
    if message_callback:
        message_callback("System", "=== Starting AutoGen Multi-Agent Code Review ===", 0)
    else:
        print("\n=== Starting AutoGen Multi-Agent Code Review ===")
    
    for round_id in range(max_rounds):
        round_num = round_id + 1
        
        if message_callback:
            message_callback("System", f"--- ROUND {round_num} ---", round_num)
        else:
            print(f"\n--- ROUND {round_num} ---")
        
        # Step 1: Reviewer review
        reviewer_prompt = review_classification_template.format(code_diff=chat_env.get("code"))
        review_comment = get_agent_response(reviewer, reviewer_prompt, reviewer_max_tokens)
        chat_env.update("comments", review_comment)
        chat_env.append_history("Reviewer", review_comment)
        
        if message_callback:
            message_callback("Reviewer", review_comment, round_num)
        else:
            print("\n Reviewer:\n", review_comment)
        
        # Step 2: Developer refinement
        developer_prompt = review_classification_template_ref.format(
            code_diff=initial_code.strip(),
            review_comment=review_comment.strip(),
            old_file=old_code.strip()
        )
        refined_code = get_agent_response(developer, developer_prompt, developer_max_tokens)
        chat_env.update_code(refined_code)
        chat_env.append_history("Developer", refined_code)
        
        if message_callback:
            message_callback("Developer", refined_code, round_num)
        else:
            print("\n Developer:\n", refined_code)
        
        # Step 3: Quality Estimation
        quality_estimation_prompt = quality_estimation_template.format(
            modified_code=refined_code.strip(),
            confidence_score=0.9
        )
        quality_estimation = get_agent_response(quality_estimator, quality_estimation_prompt, 512)
        chat_env.update("quality_estimation", quality_estimation)
        chat_env.append_history("QualityEstimator", quality_estimation)
        
        if message_callback:
            message_callback("QualityEstimator", quality_estimation, round_num)
        else:
            print("\n Quality Estimation:\n", quality_estimation)
        
        # Step 4: Comment Judge
        comment_judge_prompt = judgment_template.format(
            code_review_comment=review_comment.strip(),
            initial_code=initial_code,
            code_changes=refined_code.strip()
        )
        judgment = get_agent_response(comment_judge, comment_judge_prompt, 512)
        chat_env.update("judgment", judgment)
        chat_env.append_history("CommentJudge", judgment)
        
        if message_callback:
            message_callback("CommentJudge", judgment, round_num)
        else:
            print("\n Comment Judge:\n", judgment)
            print('judgment : ', judgment)
        
        reviewer_prompt = judgment + '### initial code: ' + initial_code + '### code changes: ' + refined_code + '### quality_estimation: ' + quality_estimation
    
    final_code = chat_env.get_code()
    
    if message_callback:
        message_callback("System", f"✅ Review Complete!\n\nFinal Refined Code:\n{final_code}", 0)
    else:
        print("\n Final Refined Code:\n", final_code)
    
    return final_code


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
