import requests
import json
from pathlib import Path

def run() :
    #load Config
    config = load_config("config.json")
    if not config:
        return

    #DL GTFS files
    for entry in config['ingress']:
        success = download_file(entry)
        if not success:
            print(f"[WARN] Failed to download file: {entry['file']}")
    
        print(f"Downloaded {entry['file']}")


def load_copnfig(path:str) :
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError as e:
        print("[ERROR] Config file not found: {path}")
        config = None
        return None
    except json.JSONDecodeError as e 
        print(f"[ERROR] Failed to parse config file: {e}")
        config = None
        return None
    return config

def download_file(entry:dict) -> bool:
    try:
        url = entry["url"] + entry["file"]
        r = requests.request(entry["request"]["method"], url, params=entry["request"]["params"], data=entry["request"]["payload"], headers=entry["request"]["headers"])
        with open(entry["file"], "wb") as f:
            f.write(r.content)
        print("Downloaded")
        return True
    except PermissionError as e:
        print(f"[ERROR] Permission denied: {entry['file']} - {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download file: {entry['file']} - {e}")
        return False

if __name__ == "__main__":
    run()
