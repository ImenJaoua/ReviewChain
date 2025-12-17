# refine_full_dataset.py
import json
import torch
import numpy as np
from tqdm import tqdm
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from util.dataset import load_dataset

from prompts.prompt import prompt as prompt

CHECKPOINT_PATH = "code_refinment"
MAX_SEQ_LENGTH = 16384
MAX_NEW_TOKENS = 256
TEST_DATA_PATH = "ref-test"
OUTPUT_REFINEMENT = "refinement_results_full.jsonl"

LANG_MAP = {
    "py": "python", "python": "python",
    "java": "java", "js": "javascript",
    "javascript": "javascript", "c": "c",
    "cpp": "cpp", "c++": "cpp"
}
SUPPORTED = set(LANG_MAP.values())

def normalize_lang(l):
    return LANG_MAP.get(l.lower().strip())

# --------------------------------------------------------------
# Load and filter dataset
# --------------------------------------------------------------
print("📂 Loading raw dataset...")
raw = load_dataset(TEST_DATA_PATH)
print(f"📊 Total examples loaded: {len(raw)}")

print("🧹 Filtering languages...")
filtered = []
for ex in raw:
    norm = normalize_lang(ex["lang"])
    if norm in SUPPORTED:
        ex["norm_lang"] = norm
        # Convert all values to strings to avoid type issues
        ex = {k: str(v) if v is not None else "" for k, v in ex.items()}
        filtered.append(ex)

print(f"➡️ {len(filtered)} supported examples found.")

dataset = Dataset.from_list(filtered)

def prepare_sample(ex):
    return {
        "prompt": prompt.format(
            code_diff=ex.get("old_hunk", "").strip(),
            review_comment=ex.get("comment", "").strip()
        ),
        "target_code": ex.get("hunk", "").strip(),
        "norm_lang": ex.get("norm_lang", "unknown").strip()
    }

print("🔄 Preparing samples...")
dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Load model
# --------------------------------------------------------------
print("\n🤖 Loading model...")
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

def clean_code(s):
    return "\n".join(line.rstrip() for line in s.strip().split("\n") if line.strip())

# --------------------------------------------------------------
# Generate refinements
# --------------------------------------------------------------
preds = []

print(f"\n🚀 Generating refinements for {len(dataset)} examples...\n")
for ex in tqdm(dataset, desc="Refining"):
    inputs = tokenizer(
        ex["prompt"],
        return_tensors="pt",
        truncation=True,
        max_length=MAX_SEQ_LENGTH
    ).to(model.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id
        )

    gen = out[0][inputs["input_ids"].shape[1]:]
    pred = clean_code(tokenizer.decode(gen, skip_special_tokens=True))

    preds.append({
        "prediction": pred,
        "reference": clean_code(ex["target_code"]),
        "lang": ex["norm_lang"]
    })

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving refinements to {OUTPUT_REFINEMENT}")
with open(OUTPUT_REFINEMENT, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print(f"\n🎉 DONE! Processed {len(preds)} examples.")
print(f"📊 Now you can run CodeBLEU score on {OUTPUT_REFINEMENT}\n")