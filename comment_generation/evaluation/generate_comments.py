import json
import torch
from tqdm import tqdm
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from prompt_template import prompt  # expects {code_diff}

CHECKPOINT_PATH = "output/checkpoint-44000"
MAX_SEQ_LENGTH = 8192
MAX_NEW_TOKENS = 128
SELECTED_FILE = "/data/rech/jaouaime/msg-test.jsonl"
OUTPUT_FILE = "comment_generation_results_alltest.jsonl"

# --------------------------------------------------------------
# Load selected examples
# --------------------------------------------------------------
print(f"📂 Loading examples from {SELECTED_FILE}")
examples = []
with open(SELECTED_FILE, "r") as f:
    for line in f:
        examples.append(json.loads(line))

dataset = Dataset.from_list(examples)

def prepare_sample(ex):
    return {
        "prompt": prompt.format(
            code_diff=ex["patch"].strip()
        ),
        "reference_comment": ex["msg"].strip()
    }

dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Load model
# --------------------------------------------------------------
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

def clean_text(s):
    return " ".join(s.strip().split())

# --------------------------------------------------------------
# Generate review comments
# --------------------------------------------------------------
preds = []

print("\n🚀 Generating review comments...\n")
for ex in tqdm(dataset, desc="CommentGen"):
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
    pred = clean_text(tokenizer.decode(gen, skip_special_tokens=True))

    preds.append({
        "prediction": pred,
        "reference": clean_text(ex["reference_comment"])
    })

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving results to {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print("\n🎉 DONE! Now you can compute BLEU on comment_generation_results.jsonl\n")
