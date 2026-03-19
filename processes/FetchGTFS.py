import zipfile
import requests
import json
from pathlib import Path

def run() :
    #load Config
    config = load_config("../config/GTFS.json")
    if not config:
        return

    #DL GTFS files
    for entry in config['ingress']:
        success = download_file(entry)
        if not success:
            print(f"[WARN] Failed to download file: {entry['file']}")
        else:
            print(f"Downloaded {entry['file']}")


def load_config(path:str) :
    try:
        with open(path) as f:
            config = json.load(f)
    except FileNotFoundError as e:
        print("[ERROR] Config file not found: {path}")
        config = None
        return None
    except json.JSONDecodeError as e: 
        print(f"[ERROR] Failed to parse config file: {e}")
        config = None
        return None
    return config

def download_file(entry:dict) -> bool:
    try:
        url = entry["url"] + entry["file"]
        # Ensure destination directory exists
        outdir = Path(f"../{entry['destDirectory']}")
        outdir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Downloading from URL: {url}")
        r = requests.request(entry["request"]["method"], url, params=entry["request"]["params"], data=entry["request"]["payload"], headers=entry["request"]["headers"])
        with open(f"../{entry['destDirectory']}{entry['destFile']}", "wb") as f:
            f.write(r.content)
        return True
    except PermissionError as e:
        print(f"[ERROR] Permission denied: {entry['file']} - {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download file: {entry['file']} - {e}")
        return False

def extract_zip(file:str, extract_to:str) -> bool:
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {file} to {extract_to}")
        return True
    except zipfile.BadZipFile as e:
        print(f"[ERROR] Bad zip file: {file} - {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to extract file: {file} - {e}")
        return False

if __name__ == "__main__":
    run()
