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

def run():
    config = ConfigHandler("../config/RT.json")
    if not config.load():
        return

    req = RequestHandler()
    th = tokenHandler()
    for entry in config.get("ingress"):
        token = th.load(entry["authority"])
        if not token:
            token=getToken(req, entry)
        else:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(token["timestamp"])
            if age > timedelta(hours=entry["authentication"]["tokenExpiry"]):
                if not entry["authentication"]["checkToken"]:
                    print(f"[DEBUG] Token expired for authority: {entry['authority']} - Age: {age}")
                    token=getToken(req, entry)
                elif not validateToken(req, token, entry):
                    print(f"[DEBUG] Token invalid for authority: {entry['authority']} - Age: {age}")
                    token=getToken(req, entry)
                else:
                    token["timestamp"] = datetime.now(timezone.utc).isoformat()
            else:
                print(f"[DEBUG] Valid token found for authority: {entry['authority']} - Token: {token}")
        for data_entry in entry["data"]:
            data=req.download_rt_file(entry["url"], data_entry, token["UserToken"])
            ph = ProtoHandler()
            
            module = ph.loadProtoClass(data_entry["class"], "../objects/protos/")
            if not module:
                print(f"[ERROR] Failed to load protobuf class: {data_entry['class']} from {data_entry['destDirectory']}")
                continue
            parsed = ph.ParseProto(module, data_entry["class"], data)
            print(f"[DEBUG] Parsed data for authority: {entry['authority']} - Data: {parsed}")

def validateToken(req: RequestHandler, token: dict, entry: dict) -> bool:
    try:
        url = entry["url"] + entry["authentication"]["checkToken"]
        print(f"[DEBUG] Loaded token for authority: {url} - {token['UserToken']}")
        r = requests.request(
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
