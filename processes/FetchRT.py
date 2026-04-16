from pathlib import Path
import sys
sys.path.append("..")
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from handlers.ConfigHandler import ConfigHandler
from handlers.RequestHandler import RequestHandler
from handlers.tokenHandler import tokenHandler
from handlers.ProtoHandler import ProtoHandler
from handlers.DBHandler import DBHandler

def run():
    config = ConfigHandler("../config/RT.json")
    if not config.load():
        return

    db_config = ConfigHandler("../config/DB.json")
    if not db_config.load():
        return

    try:
        db = DBHandler(
            host=db_config.get("host"),
            port=db_config.get("port"),
            user=db_config.get("user"),
            password=db_config.get("password"),
            database=db_config.get("database"),
        )
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return

    req = RequestHandler()
    th = tokenHandler()
    ph = ProtoHandler()

    module = ph.loadProtoClass("FeedMessage", "../objects/protos/")
    if not module:
        print("[ERROR] Failed to load protobuf module — aborting")
        db.close()
        return

    for entry in config.get("ingress"):
        authority_id = db.get_or_create_authority(entry["authority"], entry["url"])

        token = th.load(entry["authority"])
        if not token:
            token = getToken(req, entry)
        else:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(token["timestamp"])
            if age > timedelta(hours=entry["authentication"]["tokenExpiry"]):
                if not entry["authentication"]["checkToken"]:
                    print(f"[DEBUG] Token expired for authority: {entry['authority']} - Age: {age}")
                    token = getToken(req, entry)
                elif not validateToken(req, token, entry):
                    print(f"[DEBUG] Token invalid for authority: {entry['authority']} - Age: {age}")
                    token = getToken(req, entry)
                else:
                    token["timestamp"] = datetime.now(timezone.utc).isoformat()
            else:
                print(f"[DEBUG] Valid token found for authority: {entry['authority']} - Token: {token}")

        for data_entry in entry["data"]:
            data = req.download_rt_file(entry["url"], data_entry, token["UserToken"])
            if not data:
                print(f"[ERROR] Failed to download RT data for: {data_entry['endpoint']}")
                continue

            try:
                parsed = ph.ParseProto(module, "FeedMessage", data)
            except Exception as e:
                print(f"[ERROR] Failed to parse proto for {data_entry['endpoint']}: {e}")
                continue

            fetch_id = db.log_fetch(authority_id, data_entry["endpoint"], data_entry["entity"], parsed)

            try:
                db.insert_entities(authority_id, fetch_id, parsed)
                print(f"[INFO] Inserted {len(parsed.entity)} {data_entry['entity']} entities for {entry['authority']}")
            except Exception as e:
                print(f"[ERROR] DB insert failed for {data_entry['endpoint']}: {e}")

    db.close()


def validateToken(req: RequestHandler, token: dict, entry: dict) -> bool:
    try:
        url = entry["url"] + entry["authentication"]["checkToken"]
        print(f"[DEBUG] Loaded token for authority: {url} - {token['UserToken']}")
        r = req.session.request(
            entry["authentication"]["request"]["method"],
            url,
            files={"token": (None, token["UserToken"])},
            headers=entry["authentication"]["request"]["headers"],
        )
        return json.loads(r.text).get("Authenticated", "False") == "True"
    except Exception as e:
        print(f"[ERROR] Failed to validate token for authority: {entry['authority']} - {e}")
        return False


def getToken(req: RequestHandler, entry: dict) -> dict:
    try:
        th = tokenHandler()
        token = req.get_token(entry)
        token["timestamp"] = datetime.now(timezone.utc).isoformat()
        print(f"[DEBUG] Got token: {token}")
        if not th.save(json.dumps(token), entry):
            print(f"[WARN] Failed to save token for authority: {entry['authority']}")
        return token
    except Exception as e:
        print(f"[ERROR] Failed to get token for authority: {entry['authority']} - {e}")
        return None


if __name__ == "__main__":
    run()
