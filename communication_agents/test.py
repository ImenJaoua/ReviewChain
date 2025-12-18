
import sys
import json
from tqdm import tqdm
from datasets import Dataset

# Clear any cached imports
if 'phase' in sys.modules:
    del sys.modules['phase']
if 'chat_env' in sys.modules:
    del sys.modules['chat_env']

from chat_env import ChatEnv, ChatEnvConfig
from phase_with_comment import ReviewPhase

SELECTED_FILE = "evaluation/selected_50.jsonl"
OUTPUT_REFINEMENT = "refinement_results_reviewchain.jsonl"

print(f"📂 Loading selected examples from {SELECTED_FILE}")
examples = []
with open(SELECTED_FILE, "r") as f:
    for line in f:
        examples.append(json.loads(line))

dataset = Dataset.from_list(examples)

def prepare_sample(ex):
    initial_code = f"{ex['old_hunk'].strip()}\n"
    return {
        "initial_code": initial_code,
        "target_code": ex["hunk"].strip(),
        "norm_lang": ex["norm_lang"],
        "msg": ex["comment"].strip()
    }

dataset = dataset.map(prepare_sample)

# --------------------------------------------------------------
# Run ReviewChain system
# --------------------------------------------------------------

preds = []
round_stats = []

print("\n🚀 Running ReviewChain refinement...\n")

config = ChatEnvConfig(with_memory=True, test_enabled=True)

for idx, ex in enumerate(tqdm(dataset, desc="ReviewChain Refining")):
    chat_env = ChatEnv(config, ex["initial_code"])
    phase = ReviewPhase(chat_env, max_rounds=5)
    
    # Unpack the tuple returned by execute()
    refined, accepted_comment = phase.execute()
    refined = refined.strip()
    
    num_rounds = chat_env.get_iteration()
    round_stats.append(num_rounds)

    preds.append({
        "prediction": refined,
        "accepted_comment": accepted_comment,
        "msg": ex["msg"],
        "reference": ex["target_code"],
        "lang": ex["norm_lang"],
        "num_rounds": num_rounds
    })

# --------------------------------------------------------------
# Print statistics
# --------------------------------------------------------------
if round_stats:
    avg_rounds = sum(round_stats) / len(round_stats)
    max_rounds = max(round_stats)
    min_rounds = min(round_stats)
    
    print(f"\n📊 Refinement Statistics:")
    print(f"   Average rounds: {avg_rounds:.2f}")
    print(f"   Min rounds: {min_rounds}")
    print(f"   Max rounds: {max_rounds}")
    print(f"   Total examples: {len(round_stats)}")
    
    # Count how many have null comments
    null_comments = sum(1 for p in preds if p["accepted_comment"] is None)
    print(f"   Examples with null comments: {null_comments}/{len(preds)}")

# --------------------------------------------------------------
# Save results
# --------------------------------------------------------------
print(f"\n💾 Saving refinements to {OUTPUT_REFINEMENT}")
with open(OUTPUT_REFINEMENT, "w") as f:
    for row in preds:
        f.write(json.dumps(row) + "\n")

print("\n🎉 DONE! Now you can run CodeBLEU on refinement_results_reviewchain.jsonl\n")