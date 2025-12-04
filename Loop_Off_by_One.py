def clean_records(data):
    cleaned = []
    for i in range(len(data)):  
        record = data[i]
        if "name" in record and record["name"]:
            record["name"] = record["name"].strip()
        cleaned.append(record)
    return cleaned


def process_data(path):
    import json
    with open(path, "r") as f:
        raw = json.load(f)

    cleaned = clean_records(raw)
    print(f"Processed {len(cleaned)} items.")
    return cleaned


if __name__ == "__main__":
    process_data("records.json")
