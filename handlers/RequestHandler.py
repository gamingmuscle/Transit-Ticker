import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path


class RequestHandler:
    def __init__(self):
        self.session = requests.Session()

    def download_file(self, entry: dict) -> bool:
        try:
            url = entry["url"] + entry["file"]
            outdir = Path(f"../{entry['destDirectory']}")
            outdir.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] Downloading from URL: {url}")
            r = self.session.request(
                entry["request"]["method"],
                url,
                params=entry["request"]["params"],
                data=entry["request"]["payload"],
                headers=entry["request"]["headers"],
            )
            with open(f"../{entry['destDirectory']}{entry['destFile']}", "wb") as f:
                f.write(r.content)
            return True
        except PermissionError as e:
            print(f"[ERROR] Permission denied: {entry['file']} - {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to download file: {entry['file']} - {e}")
            return False

    def get_token(self, entry: dict) -> dict:
        #return json.loads('{"Authenticated": "True", "UserToken": "NJT639098140276173583"}')
        try:
            url = entry["url"] + entry["authentication"]["token"]
            print(f"[DEBUG] Downloading from URL: {url}")
            r = self.session.request(
                entry["authentication"]["request"]["method"],
                url,
                files={
                    "username": (None, entry["authentication"]["request"]["username"]),
                    "password": (None, entry["authentication"]["request"]["password"]),
                },
                headers=entry["authentication"]["request"]["headers"],
            )
            token = json.loads(r.text)
            if token["Authenticated"] != "True":
                print(f"[ERROR] Authentication failed for authority: {entry['authority']}")
                return None
            return token
        except Exception as e:
            print(f"[ERROR] Failed to get token: {e}")
            return None
    
    def validate_token(self, token: dict, entry: dict) -> bool:
        print(f"[DEBUG] Loaded token for authority: {entry['authority']} - {token}")
        age = datetime.now(timezone.utc) - datetime.fromisoformat(token["timestamp"])
        print(f"[DEBUG] Validating token for authority: {entry['authority']} - Token age: {age}")
        if not token:
            print(f"[DEBUG] No token found for authority: {entry['authority']}")
            return False
        elif (token["Authenticated"] == True or token["Authenticated"] == "True") and age < timedelta(hours=24):
            print(f"[DEBUG] Token age for authority: {entry['authority']} - Age: {age}" )
            return True
        else:
            url = entry["url"] + entry["authentication"]["checkToken"]
            print(f"[DEBUG] Loaded token for authority: {url} - {token['UserToken']}")
            r = self.session.request(
                entry["authentication"]["request"]["method"],
                url,
                files={"token": (None, token["UserToken"])},
                headers=entry["authentication"]["request"]["headers"],
            )
            response = r.text
            print(f"[DEBUG] Token validation response for authority {entry['authority']}: {response}")
            if not response:
                print(f"[DEBUG] Empty response for token validation for authority: {entry['authority']}")
                return False
            response = json.loads(response)
            if response["validToken"] != True:
                print(f"[DEBUG] Token invalid for authority: {entry['authority']}")
                return False
            token["timestamp"] = datetime.now(timezone.utc).isoformat()
            if not self.save_token(json.dumps(token), entry):
                print(f"[WARN] Failed to update token timestamp for authority: {entry['authority']}")
            return True

    def download_rt_file(self,baseurl: str, entry: dict, token: str):
        try:
            url = baseurl + entry["endpoint"]
            outdir = Path(f"../{entry['destDirectory']}")
            outdir.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] Downloading from URL: {url}")
            
            r = self.session.request(
                entry["request"]["method"],
                url,
                files={"token": (None, token)},
                headers=entry["request"]["headers"],
                allow_redirects=False,
            )
            r.raise_for_status()
            with open(f"{outdir}/{entry['destFile']}.{entry["format"]}", "wb") as f:
                f.write(r.content)
            print(f"[DEBUG] File saved: {outdir}/{entry['destFile']}.{entry["format"]}")
            return r.content
        except requests.exceptions.HTTPError as e:
            print("HTTP error:", e, "Status:", e.response.status_code)
            return False
        except PermissionError as e:
            print(f"[ERROR] Permission denied: {url} - {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to download data: {url} - {e}")
            return False
