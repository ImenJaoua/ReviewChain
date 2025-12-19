import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login

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
# GPU configuration
# ============================================================

REVIEWER_DEVICE = "cuda:0"
DEVELOPER_DEVICE = "cuda:1"
ESTIMATOR_DEVICE = "cuda:2"
FORMAT_JUDGE_DEVICE = "cuda:3"
DTYPE = torch.float16

# ============================================================
# Helper: safe model loader
# ============================================================
def load_model(model_name_or_path):
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        device_map="auto",
        torch_dtype=torch.float16
    ).eval()
    return model, tokenizer

# ============================================================
# Load models
# ============================================================
reviewer_model, reviewer_tokenizer = load_model("./models/comment_generator")
developer_model, developer_tokenizer = load_model("./models/code_refinment")
estimator_model, estimator_tokenizer = load_model("./models/quality_estimator")
# format_judge_model, format_judge_tokenizer = load_model("models/Meta-Llama-3-8B-Instruct",FORMAT_JUDGE_DEVICE)

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
            temperature=0.5,
            pad_token_id=tokenizer.eos_token_id
        )
        # Decode only the NEW tokens (excluding the input prompt)
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    # Fallback: if the above didn't work, try the old method
    if not text.strip():
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "### Response:" in text:
            text = text.split("### Response:")[-1].strip()
        elif "assistant" in text:
            text = text.split("assistant")[-1].strip()

    return text.strip()


# ============================================================
# Comment Generator Agent (A1) - NO HISTORY
# ============================================================
def comment_generator(code_diff, feedback=None, max_new_tokens=256):
    """
    A1 agent that generates comments WITHOUT conversation history.
    Each call is independent and starts fresh.
    """
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
    
    prompt = reviewer_tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate response
    comment = generate_text(
        reviewer_model, 
        reviewer_tokenizer, 
        REVIEWER_DEVICE, 
        prompt, 
        max_new_tokens
    )
    
    return comment


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
    prompt = developer_tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    return generate_text(developer_model, developer_tokenizer, DEVELOPER_DEVICE, prompt, max_new_tokens)


# ============================================================
# Quality Estimator (A3)
# ============================================================
def quality_estimator(code, max_new_tokens=256):
    system_prompt = quality_estimator_system_prompt
    user_input = quality_estimator_template.format(code_diff=code.strip())
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    prompt = estimator_tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    return generate_text(estimator_model, estimator_tokenizer, ESTIMATOR_DEVICE, prompt, max_new_tokens)


# ============================================================
# Format Judge (A4)
# ============================================================
# def format_judge(comment, max_new_tokens=256):
#     user_input = judgement_quality_template.format(comment=comment.strip())
#     messages = [
#         {"role": "system", "content": judgement_quality_system_prompt},
#         {"role": "user", "content": user_input}
#     ]

#     prompt = format_judge_tokenizer.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True
#     )

#     return generate_text(format_judge_model, format_judge_tokenizer, FORMAT_JUDGE_DEVICE, prompt, max_new_tokens)