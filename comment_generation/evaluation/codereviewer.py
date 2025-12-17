import json
import torch
from tqdm import tqdm
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "microsoft/codereviewer"
MAX_SOURCE_LENGTH = 1024
MAX_NEW_TOKENS = 128
SELECTED_FILE = "selected_200.jsonl"
OUTPUT_FILE = "comment_generation_results_codereviewer.jsonl"

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------
print(f"📂 Loading examples from {SELECTED_FILE}")
examples = []
with open(SELECTED_FILE, "r") as f:
    for line in f:
        examples.append(json.loads(line))

dataset = Dataset.from_list(examples)

def prepare_sample(ex):
    return {
        "patch": ex["patch"].strip(),
        "reference": ex["msg"].strip()
    }

dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Load CodeReviewer model
# --------------------------------------------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def clean_text(s):
    return " ".join(s.strip().split())

# --------------------------------------------------------------
# Generate review comments
# --------------------------------------------------------------
preds = []

print("\n🚀 Generating review comments with CodeReviewer...\n")
for ex in tqdm(dataset, desc="CodeReviewer"):
    inputs = tokenizer(
        ex["patch"],
        return_tensors="pt",
        truncation=True,
        max_length=MAX_SOURCE_LENGTH
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS
        )

    pred = clean_text(tokenizer.decode(outputs[0], skip_special_tokens=True))

    preds.append({
        "prediction": pred,
        "reference": clean_text(ex["reference"])
    })

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving results to {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print("\n🎉 DONE! You can now compute BLEU.\n")
