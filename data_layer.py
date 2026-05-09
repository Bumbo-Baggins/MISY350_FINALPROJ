import json
from pathlib import Path

class DataManager:
    def __init__(self, users_file="users.json", inventory_file="inventory.json"):
        self.users_file = users_file
        self.inventory_file = inventory_file

    def load_data(self, filepath, default):
        path = Path(filepath)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return default

    def save_data(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)