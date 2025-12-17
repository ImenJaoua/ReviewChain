from datasets import load_dataset, concatenate_datasets
from transformers import AutoTokenizer
import random

# ========== CONFIG ==========
path = "/data/rech/jaouaime/cls-valid.jsonl"
seed = 3
k = 8000                      # total balanced samples to keep
MAX_TOKENS = 15000             # safe limit (< model context)
model_name ="deepseek-ai/deepseek-coder-6.7b-instruct"
random.seed(seed)

# ---------- Load Tokenizer ----------
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.model_max_length = 16384
tokenizer.truncation_side = "right"

# ---------- Load Dataset ----------
print("📂 Loading dataset...")
data = load_dataset("json", data_files=path, split="train")
print("✅ Loaded", len(data), "examples")

# ---------- Filter Overlong Examples ----------
def is_within_limit(example):
    patch = example["patch"]
    n_tokens = len(tokenizer.encode(patch, add_special_tokens=False))
    if n_tokens > MAX_TOKENS:
        return False  # drop very long diffs
    return True

print(f"⚙️ Filtering examples with > {MAX_TOKENS} tokens...")
filtered_data = data.filter(is_within_limit, num_proc=8)
print(f"✅ After filtering: {len(filtered_data)} examples")

# ---------- Split by Label ----------
label0 = filtered_data.filter(lambda x: x["y"] == 0)
label1 = filtered_data.filter(lambda x: x["y"] == 1)
print(f"Label 0: {len(label0)} | Label 1: {len(label1)}")

# ---------- Balance Classes ----------
per_class = min(len(label0), len(label1), k // 2)
label0_bal = label0.shuffle(seed=seed).select(range(per_class))
label1_bal = label1.shuffle(seed=seed).select(range(per_class))

balanced_data = concatenate_datasets([label0_bal, label1_bal]).shuffle(seed=seed)
print(f"✅ Balanced dataset: {len(balanced_data)} ({per_class} per class)")

# ---------- Save Clean Subset ----------
output_path = "/data/rech/jaouaime/cls-valid-8k.jsonl"
balanced_data.to_json(output_path)
print(f"💾 Saved balanced subset to {output_path}")
