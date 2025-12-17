import datasets
import json
import csv
import pandas as pd


def load_dataset(dataset_path, split=None):
    print("Loading dataset from {}".format(dataset_path))
    dataset = datasets.load_from_disk(dataset_path)

    if split is not None and split in ["train", "valid", "test"]:
        return dataset[split]
    return dataset