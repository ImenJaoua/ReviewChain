# refine_selected_reviewchain.py
import json
from tqdm import tqdm
from datasets import Dataset

# ---- import your ReviewChain modules ----
from chat_env import ChatEnv, ChatEnvConfig
from one_round import ReviewPhase

SELECTED_FILE = "selected_50.jsonl"
OUTPUT_REFINEMENT = "results/refinement_results_reviewchain_one_round.jsonl"

print(f"📂 Loading selected examples from {SELECTED_FILE}")
examples = []
with open(SELECTED_FILE, "r") as f:
    for line in f:
        examples.append(json.loads(line))

dataset = Dataset.from_list(examples)

def prepare_sample(ex):
    """Build the ReviewChain input text."""
    initial_code = (
        f"{ex['old_hunk'].strip()}\n"
    )
    return {
        "initial_code": initial_code,
        "target_code": ex["hunk"].strip(),
        "norm_lang": ex["norm_lang"]
    }

dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Run ReviewChain system
# --------------------------------------------------------------

preds = []

print("\n🚀 Running ReviewChain refinement...\n")

config = ChatEnvConfig(with_memory=True, test_enabled=True)

for ex in tqdm(dataset, desc="ReviewChain Refining"):
    chat_env = ChatEnv(config, ex["initial_code"])
    phase = ReviewPhase(chat_env, max_rounds=5)
    refined = phase.execute().strip()

    preds.append({
        "prediction": refined
        ,"reference": ex["target_code"]
        ,"lang": ex["norm_lang"]
    })

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving refinements to {OUTPUT_REFINEMENT}")
with open(OUTPUT_REFINEMENT, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print("\n🎉 DONE! Now you can run CodeBLEU on refinement_results_reviewchain.jsonl\n")
