# select_examples.py
import json
from datasets import Dataset
from util.dataset import load_dataset

SAMPLE_SIZE = 200
SEED = 42
TEST_DATA_PATH = "ref-test"
SAVE_SELECTED = "selected_200.jsonl"

LANG_MAP = {
    "py": "python", "python": "python",
    "java": "java", "js": "javascript",
    "javascript": "javascript", "c": "c",
    "cpp": "cpp", "c++": "cpp"
}
SUPPORTED = set(LANG_MAP.values())

def normalize_lang(l):
    return LANG_MAP.get(l.lower().strip())

print("📂 Loading raw dataset...")
raw = load_dataset(TEST_DATA_PATH)

print("🧹 Filtering languages...")
filtered = []
for ex in raw:
    norm = normalize_lang(ex["lang"])
    if norm in SUPPORTED:
        ex["norm_lang"] = norm
        filtered.append(ex)

print(f"➡️ {len(filtered)} supported examples found.")

# Shuffle ONCE and select
dataset = Dataset.from_list(filtered).shuffle(SEED).select(range(SAMPLE_SIZE))

print(f"💾 Saving the {SAMPLE_SIZE} selected examples to {SAVE_SELECTED}")
with open(SAVE_SELECTED, "w") as f:
    for ex in dataset:
        f.write(json.dumps(ex) + "\n")

print("✅ DONE. Now run refine_selected.py")
