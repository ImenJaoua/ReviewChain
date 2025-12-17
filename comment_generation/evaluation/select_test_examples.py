import json
from datasets import Dataset
from util.dataset import load_dataset

SAMPLE_SIZE = 500
SEED = 42
TEST_DATA_PATH = "msg-test"
SAVE_SELECTED = "selected_200.jsonl"

print("📂 Loading raw dataset...")
raw = load_dataset(TEST_DATA_PATH)

print(f"➡️ {len(raw)} total examples found.")

# Shuffle ONCE and select
dataset = Dataset.from_list(raw).shuffle(SEED).select(range(SAMPLE_SIZE))

print(f"💾 Saving the {SAMPLE_SIZE} selected examples to {SAVE_SELECTED}")
with open(SAVE_SELECTED, "w") as f:
    for ex in dataset:
        f.write(json.dumps(ex) + "\n")

print("✅ DONE. Now run refine_selected.py")
