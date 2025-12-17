import torch
import numpy as np
from tqdm import tqdm
from typing import List
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

from util.dataset import load_dataset
from prompt_test import prompt_test
from codebleu import calc_codebleu
from datasets import Dataset

# ============================================================
# CONFIG
# ============================================================
CHECKPOINT_PATH = "code_refinment"
TEST_DATA_PATH = "ref-test"
MAX_SEQ_LENGTH = 16384
MAX_NEW_TOKENS = 256
SEED = 42
SAMPLE_SIZE = 50     # change if you want more

# ============================================================
# LOAD MODEL (4-bit)
# ============================================================
q_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model = AutoModelForCausalLM.from_pretrained(
    CHECKPOINT_PATH,
    device_map="auto",
    quantization_config=q_config,
)

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT_PATH, use_fast=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
model.config.pad_token_id = tokenizer.pad_token_id

# ============================================================
# LANGUAGE NORMALIZATION
# ============================================================
LANG_MAP = {
    "py": "python",
    "python": "python",
    "java": "java",
    "js": "javascript",
    "javascript": "javascript",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
}
SUPPORTED_LANGS = set(LANG_MAP.values())

def normalize_lang(l: str):
    return LANG_MAP.get(l.lower().strip(), None)

# Map for CodeBLEU library
CODEBLEU_LANG_MAP = {
    ".cs": "c_sharp",
    "cpp": "cpp",
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "php": "php",
    "go": "go",
    "rb": "ruby",
    "c": "c",
    "java": "java",
}

# ============================================================
# CODEBLEU HELPER
# ============================================================
def compute_codebleu(reference: str, candidate: str, lang: str) -> float:
    """
    Compute CodeBLEU robustly with graceful fallback.
    Fully compatible with Python 3.12.
    """

    mapped_lang = CODEBLEU_LANG_MAP.get(lang.lower(), None)
    if mapped_lang is None:
        print(f"[WARN] Unsupported language for CodeBLEU: {lang}")
        return 0.0

    # Try full CodeBLEU
    try:
        full = calc_codebleu(
            references=[[reference]],
            predictions=[candidate],
            lang=mapped_lang,
            weights=(0.25, 0.25, 0.25, 0.25)
        )
        if full.get("dataflow_match_score", 0) > 0:
            return full["codebleu"]
        raise Exception("Dataflow parser unavailable")
    except Exception:
        pass

    # Try without dataflow
    try:
        partial = calc_codebleu(
            references=[[reference]],
            predictions=[candidate],
            lang=mapped_lang,
            weights=(1/3, 1/3, 1/3, 0.0)
        )
        return partial["codebleu"]
    except Exception:
        pass

    # N-gram only
    try:
        ngram = calc_codebleu(
            references=[[reference]],
            predictions=[candidate],
            lang=mapped_lang,
            weights=(1.0, 0.0, 0.0, 0.0)
        )
        return ngram.get("ngram_match_score", 0.0)

    except Exception as e:
        print("[ERROR] CodeBLEU failed completely:", e)
        return 0.0

# ============================================================
# LOAD & FILTER DATA
# ============================================================
raw_ds = load_dataset(TEST_DATA_PATH)
print("Loaded dataset:", len(raw_ds))

filtered = []
for ex in raw_ds:
    norm = normalize_lang(ex["lang"])
    if norm in SUPPORTED_LANGS:
        ex["norm_lang"] = norm
        filtered.append(ex)

print("Filtered dataset:", len(filtered))

dataset = Dataset.from_list(filtered).shuffle(seed=SEED)
dataset = dataset.select(range(SAMPLE_SIZE))

# ============================================================
# FORMAT INPUT FOR LLMS
# ============================================================
def prepare_sample(ex):
    return {
        "prompt": prompt_test.format(
            code_diff=ex["old_hunk"].strip(),
            review_comment=ex["comment"].strip()
        ),
        "target_code": ex["hunk"].strip(),
        "norm_lang": ex["norm_lang"]
    }

dataset = dataset.map(prepare_sample)

# ============================================================
# CLEAN UP CODE OUTPUT
# ============================================================
def clean_code(s: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in s.strip().split("\n")
        if line.strip()
    )

# ============================================================
# GENERATE REFINED CODE
# ============================================================
model.eval()
predictions, references, langs = [], [], []

print("\nGenerating predictions...\n")
for ex in tqdm(dataset, desc="Refining code"):
    inputs = tokenizer(
        ex["prompt"],
        return_tensors="pt",
        truncation=True,
        max_length=MAX_SEQ_LENGTH
    ).to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id
        )

    gen_ids = output[0][inputs["input_ids"].shape[1]:]
    pred = tokenizer.decode(gen_ids, skip_special_tokens=True)

    predictions.append(clean_code(pred))
    references.append(clean_code(ex["target_code"]))
    langs.append(ex["norm_lang"])

# ============================================================
# EVALUATE
# ============================================================
scores = []
for ref, pred, lang in zip(references, predictions, langs):
    score = compute_codebleu(ref, pred, lang)
    scores.append(score)

print("\n================ CODEBLEU RESULTS ================")
print(f"Samples evaluated: {len(scores)}")
print(f"Avg CodeBLEU: {np.mean(scores):.4f}")
print("==================================================\n")
