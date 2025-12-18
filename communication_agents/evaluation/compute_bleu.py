from util.dataset import load_jsonl_file
import sacrebleu


data = load_jsonl_file("refinement_results_reviewchain_one_round.jsonl")

preds = [d["comment"] for d in data]
refs  = [d["msg"] for d in data]

# BLEU
bleu = sacrebleu.corpus_bleu(preds, [refs])
print(f"BLEU: {bleu.score:.2f}")

