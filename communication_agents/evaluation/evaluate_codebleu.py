import json
import numpy as np
from codebleu import calc_codebleu

# ============================================================
# CONFIG
# ============================================================
RESULTS_PATH = "refinement_results_reviewchain_one_round.jsonl"

CODEBLEU_LANG_MAP = {
    "python": "python", "java": "java", "cpp": "cpp",
    "c": "c", "javascript": "javascript", "js": "javascript",
    "php": "php", "go": "go", "ruby": "ruby"
}

# ============================================================
# LOAD REFINEMENT OUTPUTS
# ============================================================
rows = []
with open(RESULTS_PATH) as f:
    for line in f:
        rows.append(json.loads(line))

print(f"Loaded {len(rows)} refinement results.")

# ============================================================
# CODEBLEU WITH FALLBACK
# ============================================================
def compute_codebleu(ref, pred, lang):
    mapped = CODEBLEU_LANG_MAP.get(lang, None)
    if mapped is None:
        return 0.0

    try:
        bleu = calc_codebleu(
            references=[[ref]],
            predictions=[pred],
            lang=mapped,
            weights=(0.25, 0.25, 0.25, 0.25)
        )

        # Fallback when dataflow fails
        if bleu.get("dataflow_match_score", 0) == 0:
            bleu = calc_codebleu(
                references=[[ref]],
                predictions=[pred],
                lang=mapped,
                weights=(1/3, 1/3, 1/3, 0.0)
            )

        return bleu["codebleu"]

    except Exception:
        return 0.0

# ============================================================
# EVALUATE ALL
# ============================================================
scores = []
for row in rows:
    s = compute_codebleu(row["reference"], row["prediction"], row["lang"])
    scores.append(s)

print("\n================ CODEBLEU RESULTS ================")
print(f"Samples evaluated: {len(scores)}")
print(f"Avg CodeBLEU: {np.mean(scores):.4f}")
print("==================================================\n")
