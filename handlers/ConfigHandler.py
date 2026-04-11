import json


class ConfigHandler:
    def __init__(self, path: str):
        self.path = path
        self.config = None

    def load(self) -> bool:
        try:
            with open(self.path) as f:
                self.config = json.load(f)
            return True
        except FileNotFoundError:
            print(f"[ERROR] Config file not found: {self.path}")
            return False
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse config file: {e}")
            return False

    def get(self, key: str = None):
        if key is None:
            return self.config
        return self.config.get(key) if self.config else None
