import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from tqdm import tqdm
import evaluate
from util.dataset import load_dataset
from prompt_templates import prompt

# ========== CONFIG ==========
checkpoint_path = "output/checkpoint-8000"
test_data_path = "cls-test"   # your test dataset name or file
max_seq_length = 16384
max_new_tokens = 128  # adjust depending on your task

# ========== LOAD MODEL ==========
q_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    checkpoint_path,
    device_map="auto",
    quantization_config=q_config
)
tokenizer = AutoTokenizer.from_pretrained(checkpoint_path, use_fast=True)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
model.config.pad_token_id = tokenizer.pad_token_id

# ========== LOAD TEST DATA ==========
test_data = load_dataset(test_data_path)
test_data = test_data.shuffle(seed=42).select(range(3000))

def format_prompt(example):
    user_input = prompt.format(code_diff=example["patch"].strip())
    return {
        "prompt": user_input,
        "completion": str(example["y"]).strip()
    }

test_ds = test_data.map(format_prompt, remove_columns=test_data.column_names)

# ========== GENERATE PREDICTIONS ==========
model.eval()
predictions = []
references = []

for example in tqdm(test_ds, desc="Evaluating"):
    inputs = tokenizer(
        example["prompt"],
        return_tensors="pt",
        truncation=True,
        max_length=max_seq_length
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens,pad_token_id=tokenizer.pad_token_id)
    
    pred = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    print(pred)
    predictions.append(pred.strip())
    references.append(example["completion"])

# ========== COMPUTE METRICS ==========
# Example: accuracy (if your output is categorical)
metric = evaluate.load("accuracy")
precision_metric = evaluate.load("precision")
recall_metric = evaluate.load("recall")
f1_metric = evaluate.load("f1")
acc = metric.compute(predictions=predictions, references=references)["accuracy"]
precision = precision_metric.compute(predictions=predictions, references=references)["precision"]
recall = recall_metric.compute(predictions=predictions, references=references)["recall"]
f1 = f1_metric.compute(predictions=predictions, references=references)["f1"]
print("📊 Evaluation Metrics:")
print(f"Accuracy: {acc:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")

