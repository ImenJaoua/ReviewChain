from datasets import Dataset
from transformers import AutoTokenizer
import json, random

# ========== CONFIG ==========
path = "/data/rech/jaouaime/ref-valid.jsonl"
output_path = "/data/rech/jaouaime/ref-valid-10k.jsonl"
seed = 3
MAX_TOKENS = 15000             # safe limit (< model context)
MAX_EXAMPLES = 10000
model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"

random.seed(seed)

# ---------- Load Tokenizer ----------
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.model_max_length = 16384
tokenizer.truncation_side = "right"

# ---------- Safe Load Dataset ----------
print("📂 Loading dataset safely...")
data_list = []
with open(path, "r") as f:
    for line in f:
        try:
            ex = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip broken lines

        # Normalize fields to avoid ArrowInvalid errors
        if "ids" in ex:
            if isinstance(ex["ids"], (int, float)):
                ex["ids"] = str(ex["ids"])
            elif isinstance(ex["ids"], list):
                ex["ids"] = [str(x) for x in ex["ids"]]

        data_list.append(ex)

print(f"✅ Loaded {len(data_list)} examples")
data = Dataset.from_list(data_list)

# ---------- Filter Overlong Examples ----------
def is_within_limit(example):
    old_hunk = example.get("old_hunk", "")
    new_hunk = example.get("hunk", "")
    combined = f"{old_hunk}\n{new_hunk}"       # ✅ count both together
    n_tokens = len(tokenizer.encode(combined, add_special_tokens=False))
    return n_tokens <= MAX_TOKENS

print(f"⚙️ Filtering examples where old_hunk + hunk > {MAX_TOKENS} tokens...")
filtered_data = data.filter(is_within_limit, num_proc=8)
print(f"✅ After filtering: {len(filtered_data)} examples")

# ---------- Limit to MAX_EXAMPLES ----------
if len(filtered_data) > MAX_EXAMPLES:
    filtered_data = filtered_data.shuffle(seed=seed).select(range(MAX_EXAMPLES))
    print(f"✅ Randomly selected {MAX_EXAMPLES} examples")
else:
    print("ℹ️ Dataset smaller than {MAX_EXAMPLES}; keeping all examples.")

# ---------- Save Clean Subset ----------
filtered_data.to_json(output_path)
print(f"💾 Saved filtered subset to {output_path}")
