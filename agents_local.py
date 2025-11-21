# agents_local.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel
from comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref, 
)

from comment_prompt_AUTOMAT import (
    review_classification_system_prompt as review_classification_system_prompt_auto,
    review_classification_template as review_classification_template_auto,
)

from comment_prompt_chain_zero import (
    review_classification_system_prompt as review_classification_system_prompt_cz,
    review_classification_template as review_classification_template_cz,
)

from comment_prompt_chain_few import (
    review_classification_system_prompt as review_classification_system_prompt_cf,
    review_classification_template as review_classification_template_cf,
)

from comment_prompt_Meta import (
    review_classification_system_prompt as review_classification_system_prompt_meta,
    review_classification_template as review_classification_template_meta,
)



def load_model(model_name_or_path):

    

    # ======= LOAD MODEL =======
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
    model_name_or_path,
    device_map="auto",
    torch_dtype=torch.float16
    ).eval()

    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    

    return generator


# === Agents ===
reviewer_generator = load_model("trained_model_A1")   # A1: Reviewer
developer_generator = load_model("deepseek-ai/deepseek-coder-6.7b-instruct")  # A2: Developer


def comment_generator(code_diff,max_new_tokens = 256):
    generator = reviewer_generator
    tokenizer = AutoTokenizer.from_pretrained("trained_model_A1", use_fast=True)

    # ======= BUILD PROMPT =======
    system_prompt = review_classification_system_prompt
    user_input = review_classification_template.format(code_diff=code_diff.strip())

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # ======= GENERATE =======
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        return_full_text=False
    )

    return response[0]["generated_text"]


def code_refiner(code_diff, comment,oldf="", max_new_tokens = 256):
    generator = developer_generator
    tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-6.7b-instruct", use_fast=True)

    # ======= BUILD PROMPT =======
    system_prompt = review_classification_system_prompt_ref
    user_input = review_classification_template_ref.format(code_diff=code_diff.strip(), review_comment=comment.strip(), old_file=oldf.strip())

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # ======= GENERATE =======
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        return_full_text=False
    )

    return response[0]["generated_text"]

