# refine_selected_reviewchain_one_round.py

import json
from tqdm import tqdm
from datasets import Dataset

# ---- import your ReviewChain modules ----
from chat_env import ChatEnv, ChatEnvConfig
from one_round import ReviewPhase   # your new single-round ReviewPhase

SELECTED_FILE = "selected_200.jsonl"
OUTPUT_REFINEMENT = "results/refinement_results_reviewchain_200.jsonl"

print(f"📂 Loading selected examples from {SELECTED_FILE}")
examples = []
with open(SELECTED_FILE, "r") as f:
    for line in f:
        examples.append(json.loads(line))

dataset = Dataset.from_list(examples)

# --------------------------------------------------------------
# Prepare dataset samples
# --------------------------------------------------------------

def prepare_sample(ex):
    """
    Build the ReviewChain input text.
    For the one-round mode, only the initial code is passed.
    """
    initial_code = ex["old_hunk"].strip()
    return {
        "initial_code": initial_code,
        "target_code": ex["hunk"].strip(),
        "norm_lang": ex["norm_lang"]
    }

dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Run ONE-ROUND ReviewChain system
# --------------------------------------------------------------

preds = []

print("\n🚀 Running ReviewChain single-round refinement...\n")

config = ChatEnvConfig(with_memory=True, test_enabled=True)

for ex in tqdm(dataset, desc="ReviewChain Single-Round"):
    # Create a fresh chat environment with the initial code
    chat_env = ChatEnv(config, ex["initial_code"])

    # ONE-ROUND ReviewPhase, no need to pass max_rounds
    phase = ReviewPhase(chat_env)

    refined = phase.execute().strip()

    preds.append({
        "prediction": refined,
        "reference": ex["target_code"],
        "lang": ex["norm_lang"]
    })

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving refinements to {OUTPUT_REFINEMENT}")
with open(OUTPUT_REFINEMENT, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print("\n🎉 DONE! Now you can run CodeBLEU on refinement_results_reviewchain_one_round.jsonl\n")
