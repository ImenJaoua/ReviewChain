import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref,
)
from quality_estimator import (
    quality_estimator_system_prompt,
    quality_estimator_template,
)
from comment_prompt_round2 import (
    review_classification_template2, 
    review_classification_system_prompt2
)
# ============================================================
# GPU configuration
# ============================================================


REVIEWER_DEVICE = "cuda:0"
DEVELOPER_DEVICE = "cuda:1"
ESTIMATOR_DEVICE = "cuda:2"  # share with Reviewer
DTYPE = torch.float16


# ============================================================
# Helper: safe model loader
# ============================================================
def load_model(model_name_or_path, device):
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        dtype=DTYPE,
        device_map={ "": device }  # place entire model on this device
    ).eval()
    return model, tokenizer


# ============================================================
# Load Reviewer (A1) and Developer (A2) and Estimator (A3) models
# ============================================================
reviewer_model, reviewer_tokenizer = load_model("trained_model_A1", REVIEWER_DEVICE)
developer_model, developer_tokenizer = load_model("code_refinment", DEVELOPER_DEVICE)
estimator_model, estimator_tokenizer = load_model("quality_estimator", ESTIMATOR_DEVICE)

# ============================================================
# Helper: generation
# ============================================================
def generate_text(model, tokenizer, device, prompt, max_new_tokens=256):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # === Extract only the assistant's response after "### Response:" ===
    if "### Response:" in text:
        text = text.split("### Response:")[-1].strip()

    return text


# ============================================================
# Reviewer Agent (A1)
# ============================================================
def comment_generator(code_diff= None,feedback=None, previous_code=None, max_new_tokens=256):
    # First round: standard comment generation
    if feedback is None:
        system_prompt = review_classification_system_prompt
        user_input = review_classification_template.format(code_diff=code_diff.strip())
    else:
        # Subsequent rounds: include feedback context
        system_prompt = review_classification_system_prompt2
        feedback_context = review_classification_template2.format(
            code_diff=feedback['previous_code'],
            previous_comments=feedback['previous_comments'],
            justification=feedback['justification']
        )

        user_input = feedback_context
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    prompt = reviewer_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return generate_text(reviewer_model, reviewer_tokenizer, REVIEWER_DEVICE, prompt, max_new_tokens)
# ============================================================
# Developer Agent (A2)
# ============================================================
def code_refiner(code_diff, comment, max_new_tokens=256):
    system_prompt = review_classification_system_prompt_ref
    user_input = review_classification_template_ref.format(
        code_diff=code_diff.strip(),
        review_comment=comment.strip(),
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    prompt = developer_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return generate_text(developer_model, developer_tokenizer, DEVELOPER_DEVICE, prompt, max_new_tokens)
# ============================================================
# Quality Estimator Agent (A3)
# ============================================================
def quality_estimator(refined_code, max_new_tokens=512):
    system_prompt = quality_estimator_system_prompt
    user_input = quality_estimator_template.format(
        code_diff=refined_code.strip(),
        
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    prompt = estimator_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return generate_text(estimator_model, estimator_tokenizer, ESTIMATOR_DEVICE, prompt, max_new_tokens)