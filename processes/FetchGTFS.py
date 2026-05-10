import zipfile
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from handlers.ConfigHandler import ConfigHandler
from handlers.RequestHandler import RequestHandler
from handlers.GTFSHandler import GTFSHandler
from handlers.DBHandler import DBHandler


def run():
    config = ConfigHandler(os.path.join(_ROOT, "config", "GTFS.json"))
    if not config.load():
        return

    try:
        db = DBHandler.from_env()
    except KeyError as e:
        print(f"[ERROR] Missing required environment variable: {e}")
        return

    req = RequestHandler()
    for entry in config.get("ingress"):
        if not req.download_file(entry):
            print(f"[WARN] Failed to download file: {entry['file']}")
            continue

        zip_path = os.path.join(_ROOT, entry['destDirectory'], entry['destFile'])
        print(f"Downloaded {entry['file']} — loading into DB...")
        load_zip(db, zip_path, entry["agency_id"])

    db.close()


def load_zip(db: DBHandler, zip_path: str, agency_id: str):
    try:
        handler = GTFSHandler(zip_path)
    except Exception as e:
        print(f"[ERROR] Failed to open zip: {zip_path} - {e}")
        return

    present = handler.get_files()

    for filename in GTFSHandler.LOAD_ORDER:
        if filename not in present:
            print(f"[SKIP] {filename} not in zip")
            continue

        mapping = GTFSHandler.FILE_TABLE_MAP[filename]
        table   = mapping['table']
        columns = mapping['columns']
        inject  = mapping['inject_agency_id']

        rows = _build_rows(handler.read_file(filename), columns, inject, agency_id)

        try:
            count = db.bulk_insert(table, columns, rows, replace=True)
            db.commit()
            print(f"  Loaded {count} rows into {table}")
        except Exception as e:
            print(f"[ERROR] Failed to insert into {table}: {e}")

    handler.close()


def _build_rows(csv_rows, columns: list[str], inject_agency_id: bool, agency_id: str):
    """Yield row tuples aligned to columns. Injects agency_id where the CSV omits it."""
    for row in csv_rows:
        yield tuple(
            agency_id if (inject_agency_id and col == 'agency_id') else (row.get(col) or None)
            for col in columns
        )


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
