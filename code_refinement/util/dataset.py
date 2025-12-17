import datasets
import json
import pandas as pd


def load_dataset(dataset_path, split=None):
    print("Loading dataset from {}".format(dataset_path))
    dataset = datasets.load_from_disk(dataset_path)

    if split is not None and split in ["train", "valid", "test"]:
        return dataset[split]
    return dataset

def load_jsonl_file(file_path):
    print("Loading dataset from {}".format(file_path))
    data = None
    with open(file_path) as lines:
        data = [json.loads(line) for line in lines]
    for d in data:
        if 'ids' in d:
            d['ids'] = list(map(str, d['ids']))
    print("Dataset size = {}".format(len(data)))
    return data

def load_CRdatasets(dataset_file):
    data = load_jsonl_file(dataset_file)
  
    return data

def create_HFdataset(dataset_file, output_dir, seed=0):
    data = load_CRdatasets(dataset_file)
    dataset = datasets.Dataset.from_list(data)
    print("Dataset features = {}".format(dataset.column_names))
    print("Total datasets size = {}".format(len(dataset)))
    dataset = dataset.shuffle(seed=seed)
    dataset.save_to_disk(output_dir)


def save_jsonl_file(data, file_path):
    with open(file_path, 'w') as f:
        for d in data:
            f.write(json.dumps(d) + '\n')

