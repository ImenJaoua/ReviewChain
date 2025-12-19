# agents_local.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel

from prompts_template.comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from prompts_template.format_round import (
    review_format_system_prompt,
    review_format_prompt,
)
from prompts_template.ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref,
)
from prompts_template.quality_estimator import (
    quality_estimator_system_prompt,
    quality_estimator_template,
)
from prompts_template.comment_prompt_round2 import (
    review_classification_system_prompt2,
    review_classification_prompt2,
)
from prompts_template.judge_format_prompt import (
    judgement_quality_system_prompt,
    judgement_quality_template,
)

# ============================================================
# Helper: model loader
# ============================================================
def load_model(model_name_or_path):
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        device_map="auto",
        torch_dtype=torch.float16
    ).eval()
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    
    return generator

# ============================================================
# Load models
# ============================================================
reviewer_generator = load_model("./models/trained_model_A1")
developer_generator = load_model("./models/code_refinment")
estimator_generator = load_model("./models/quality_estimator")
# format_judge_generator = load_model("models/Meta-Llama-3-8B-Instruct")

# ============================================================
# Comment Generator Agent (A1) - NO HISTORY
# ============================================================
def comment_generator(code_diff, feedback=None, max_new_tokens=256):
    """
    A1 agent that generates comments WITHOUT conversation history.
    Each call is independent and starts fresh.
    """
    generator = reviewer_generator
    tokenizer = AutoTokenizer.from_pretrained("./models/trained_model_A1", use_fast=True)
    
    # Determine which system prompt and user message to use
    if feedback is None:
        # FIRST ROUND
        system_prompt = review_classification_system_prompt
        user_message = review_classification_template.format(
            code_diff=code_diff.strip()
        )

    elif feedback.get("source") == "format":
        # FORMAT REJECTION - emphasize format requirements
        system_prompt = review_format_system_prompt
        user_message = review_format_prompt.format(
            code_diff=feedback["previous_code"],
            previous_comments=feedback["previous_comments"],
            justification=feedback["justification"]
        )

    else:
        # QUALITY REJECTION
        system_prompt = review_classification_system_prompt2
        user_message = review_classification_prompt2.format(
            code_diff=feedback["previous_code"],
            previous_comment=feedback["previous_comments"],
            justification=feedback["justification"]
        )
    
    # Build prompt (no history, just current message)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate response
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        return_full_text=False
    )
    
    return response[0]["generated_text"]


# ============================================================
# Developer Agent (A2)
# ============================================================
def code_refiner(code_diff, comment, max_new_tokens=256):
    generator = developer_generator
    tokenizer = AutoTokenizer.from_pretrained("./models/code_refinment", use_fast=True)
    
    system_prompt = review_classification_system_prompt_ref
    user_input = review_classification_template_ref.format(
        code_diff=code_diff.strip(),
        review_comment=comment.strip(),
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate response
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        return_full_text=False
    )
    
    return response[0]["generated_text"]


# ============================================================
# Quality Estimator (A3)
# ============================================================
def quality_estimator(code, max_new_tokens=256):
    generator = estimator_generator
    tokenizer = AutoTokenizer.from_pretrained("./models/quality_estimator", use_fast=True)
    
    system_prompt = quality_estimator_system_prompt
    user_input = quality_estimator_template.format(code_diff=code.strip())
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate response
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        return_full_text=False
    )
    
    return response[0]["generated_text"]


# ============================================================
# Format Judge (A4)
# ============================================================
# def format_judge(comment, max_new_tokens=256):
#     generator = format_judge_generator
#     tokenizer = AutoTokenizer.from_pretrained("models/Meta-Llama-3-8B-Instruct", use_fast=True)
#     
#     user_input = judgement_quality_template.format(comment=comment.strip())
#     messages = [
#         {"role": "system", "content": judgement_quality_system_prompt},
#         {"role": "user", "content": user_input}
#     ]
#
#     prompt = tokenizer.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True
#     )
#
#     # Generate response
#     response = generator(
#         prompt,
#         max_new_tokens=max_new_tokens,
#         return_full_text=False
#     )
#     
#     return response[0]["generated_text"]