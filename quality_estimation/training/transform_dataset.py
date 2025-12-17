from util.dataset import load_jsonl_file, create_HFdataset
from config import ExLlamaArguments
from transformers import HfArgumentParser




parser = HfArgumentParser(ExLlamaArguments)
model_args = parser.parse_args_into_dataclasses()[0]

dataset_path = model_args.dataset_path


create_HFdataset(dataset_path, "cls-test")