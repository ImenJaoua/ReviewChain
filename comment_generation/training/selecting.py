from datasets import load_dataset
from transformers import AutoTokenizer
import random
from collections import defaultdict

# ========== CONFIG ==========
HF_DATASET = "OussamaBS/CuREV"
output_path = "/data/rech/jaouaime/comment-valid-6k.jsonl"

seed = 3
MAX_TOKENS = 15000
MAX_EXAMPLES = 6000
MIN_PER_LANG = 500     # minimum guaranteed samples per language

model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
random.seed(seed)

# ---------- Load Tokenizer ----------
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.model_max_length = 16384
tokenizer.truncation_side = "right"

# ---------- Load Dataset ----------
dataset = load_dataset(HF_DATASET, split="validation")

# ---------- Normalize "ids" ----------
def normalize(example):
    if "ids" in example:
        if isinstance(example["ids"], (int, float)):
            example["ids"] = str(example["ids"])
        elif isinstance(example["ids"], list):
            example["ids"] = [str(x) for x in example["ids"]]
    return example

dataset = dataset.map(normalize)

# ---------- Token Filtering ----------
def is_within_limit(example):
    combined = f"{example.get('code_diff','')}\n{example.get('reformulated_comment','')}"
    n_tokens = len(tokenizer.encode(combined, add_special_tokens=False))
    return n_tokens <= MAX_TOKENS

filtered = dataset.filter(is_within_limit, num_proc=8)

# ---------- Guarantee all languages appear ----------
print("📊 Guaranteeing all languages...")

# group examples by lang
lang_to_indices = defaultdict(list)
for i, ex in enumerate(filtered):
    lang_to_indices[ex["lang"]].append(i)

# check available languages
langs = list(lang_to_indices.keys())
print("Languages found:", langs)

# take MIN_PER_LANG or as many as exist
guaranteed_indices = []
for lang, idxs in lang_to_indices.items():
    random.shuffle(idxs)
    take = min(len(idxs), MIN_PER_LANG)
    guaranteed_indices.extend(idxs[:take])

print(f"Guaranteed {len(guaranteed_indices)} base examples")

# ---------- Fill up to MAX_EXAMPLES with random samples ----------
remaining_needed = MAX_EXAMPLES - len(guaranteed_indices)
print("Need to add:", remaining_needed)

all_indices = list(range(len(filtered)))
random.shuffle(all_indices)

# exclude ones already taken
remaining_pool = [i for i in all_indices if i not in guaranteed_indices]

# sample the remaining
extra_indices = remaining_pool[:remaining_needed]

# combine
final_indices = guaranteed_indices + extra_indices

# remove duplicates
final_indices = list(dict.fromkeys(final_indices))

# shuffle final dataset
random.shuffle(final_indices)

# ---------- Select subset ----------
final_data = filtered.select(final_indices[:MAX_EXAMPLES])

print(f"🔥 Final dataset size: {len(final_data)}")
print(f"🌍 Languages included: {set([ex['lang'] for ex in final_data])}")

# ---------- Save ----------
final_data.to_json(output_path)
print("💾 Saved to:", output_path)
