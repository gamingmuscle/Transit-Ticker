import zipfile
import sys
sys.path.append("..")

from handlers.ConfigHandler import ConfigHandler
from handlers.RequestHandler import RequestHandler


def run():
    config = ConfigHandler("../config/GTFS.json")
    if not config.load():
        return

    req = RequestHandler()
    for entry in config.get("ingress"):
        if not req.download_file(entry):
            print(f"[WARN] Failed to download file: {entry['file']}")
        else:
            print(f"Downloaded {entry['file']}")


def extract_zip(file: str, extract_to: str) -> bool:
    try:
        with zipfile.ZipFile(file, "r") as zip_ref:
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
