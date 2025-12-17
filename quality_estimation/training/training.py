import os
import re
import glob
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, HfArgumentParser, BitsAndBytesConfig, EarlyStoppingCallback
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig
from config import ExLlamaArguments
from prompt_templates import prompt
from util.dataset import load_dataset

# ============================================================
#                   ENVIRONMENT & SEED
# ============================================================
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
torch.manual_seed(27)
transformers.set_seed(27)

# ============================================================
#                   ARGUMENTS
# ============================================================
parser = HfArgumentParser(ExLlamaArguments)
model_args = parser.parse_args_into_dataclasses()[0]

model_name_or_path = model_args.model_name_or_path
dataset_path = model_args.dataset_path
output_path = model_args.output_path
checkpoint_path = model_args.checkpoint_path
batch_size = model_args.batch_size
max_seq_length = model_args.max_seq_len
save_steps = model_args.save_steps
num_epochs = model_args.num_epochs
continue_from_checkpoint = model_args.continue_from_checkpoint
# ============================================================
#                   MODEL & TOKENIZER
# ============================================================
model_kwargs = {
    "low_cpu_mem_usage": True,
    "trust_remote_code": False,
    "dtype": torch.float16   # ✅ fixed key name
}

q_config = BitsAndBytesConfig(
   load_in_4bit=True,
   bnb_4bit_quant_type="nf4",
   bnb_4bit_use_double_quant=True,
   bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    model_name_or_path,
    **model_kwargs,
    attn_implementation="flash_attention_2",
    device_map="auto",
    quantization_config=q_config
)

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

model.config.pad_token_id = tokenizer.pad_token_id
model.generation_config.pad_token_id = tokenizer.pad_token_id
# ============================================================
#                   LORA CONFIGURATION
# ============================================================
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
# Early stopping callback
callbacks = EarlyStoppingCallback(early_stopping_patience=3)
# ============================================================
#                   LOAD & FORMAT DATA
# ============================================================
data= load_dataset("cls-train-balanced-80k")
valid_data = load_dataset("cls-valid-8k")   # your separate valid set

print(f"✅ Dataset size: {len(data)}")
print(f"✅ valid Dataset size: {len(valid_data)}")

print(f"Dataset features: {data.column_names}")

def format_prompt(example):
    """Build chat-formatted text + completion fields"""
    user_input = prompt.format(code_diff=example["patch"].strip())

  
    return {
        "prompt": user_input,
        "completion": str(example["y"]).strip()  # ✅ fixed (no loop variable)
    }

# ✅ map expects a dict return per row, not a list
dataset = data.map(format_prompt, remove_columns=data.column_names)
valid_ds = valid_data.map(format_prompt, remove_columns=valid_data.column_names)

print("✅ Example formatted entry:\n", dataset[0])

# ============================================================
#                   SFT CONFIG
# ============================================================
sft_config = SFTConfig(
    output_dir=output_path,
    gradient_accumulation_steps=4,
    num_train_epochs=num_epochs,
    save_steps=save_steps,
    logging_steps=200,
    per_device_train_batch_size=batch_size,
    bf16=True,
    report_to="none",
    dataset_text_field= "prompt",
    completion_only_loss=True,   # ✅ only train on assistant part
    eval_strategy="steps",   # run periodic validation
    eval_steps=2000,
    save_strategy="steps",
    load_best_model_at_end=True,


)


# ============================================================
#                   TRAINER
# ============================================================
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,           
    train_dataset=dataset,
    eval_dataset= valid_ds, 
    args=sft_config,
    peft_config=peft_config,
    callbacks=[callbacks],
)

# Optional: inspect a single batch
train_dataloader = trainer.get_train_dataloader()
for batch in train_dataloader:
    input_ids = batch["input_ids"][0]
    labels = batch["labels"][0]
    print("Decoded example:\n", tokenizer.decode(input_ids))
    print("Masked labels:", labels)
    break

# ============================================================
#                   TRAINING
# ============================================================
 # Clear GPU memory cache
torch.cuda.empty_cache()
    # Sorting checkpoints function
def sort_checkpoints(checkpoint_paths):
    def extract_checkpoint_number(checkpoint_path):
            match = re.search(r'checkpoint-(\d+)', checkpoint_path)
            return int(match.group(1)) if match else float('inf')
    return sorted(checkpoint_paths, key=extract_checkpoint_number)

    # Continue training from the latest checkpoint if provided
if continue_from_checkpoint:
    checkpoint_path = os.path.join('./output2', "checkpoint-*")
    checkpoints = sort_checkpoints(glob.glob(checkpoint_path))
        
    print(f"Found checkpoints: {checkpoints}")
        
    if checkpoints:
            checkpoint = checkpoints[-1]  # Get the most recent checkpoint
            print(f"Resuming from checkpoint: {checkpoint}")
            trainer.train(resume_from_checkpoint=checkpoint)
    else:
            print("No checkpoint found. Starting training from scratch.")
            trainer.train()
else:
        print("Starting training from scratch.")
        trainer.train()