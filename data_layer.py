import json
from pathlib import Path

def load_json(filepath, default_data):
    path = Path(filepath)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return default_data

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)