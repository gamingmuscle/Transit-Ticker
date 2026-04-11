import json
from pathlib import Path


class tokenHandler:
    def load(self, auth: str) -> dict:
        try:
            return json.loads(Path(f"../tokens/{auth}.json").read_text())
        except FileNotFoundError:
            print(f"[ERROR] Token file not found: ../tokens/{auth}.json")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse token file ({auth}.json): {e}")
            return 
        
    def save(self, token: str, entry: dict) -> bool:
        try:
            outdir = Path("../tokens/")
            outdir.mkdir(parents=True, exist_ok=True)
            with open(f"../tokens/{entry['authority']}.json", "w") as f:
                f.write(token)
            return True
        except PermissionError as e:
            print(f"[ERROR] Permission denied: ../tokens/{entry['authority']}.json - {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to save token: ../tokens/{entry['authority']}.json - {e}")
            return False
    