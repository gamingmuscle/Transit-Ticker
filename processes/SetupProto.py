import requests
import json
from pathlib import Path
from datetime import datetime, timezone


def CheckProto(proto:str, destDir:str) -> bool:
    try:
        CACHE_DIR = Path(destDir)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        pfile = CACHE_DIR / f"{proto}.py"
        if not pfile.exists():
            return False
        return True
    except ImportError as e:
        print(f"[ERROR] Protobuf library not found: {e}")
        return False
    
def GenerateProtoClass(proto:str, protoDir:str) -> bool:
    try:
        temp_proto_path =  Path( protoDir) / (proto + ".proto")
        # Compile the proto file using protoc
        import subprocess
        print(f"[DEBUG] Compiling proto file: protoc --proto_path={protoDir} --python_out={protoDir} - {temp_proto_path}")
        result = subprocess.run(["protoc", f"--proto_path={protoDir}", f"--python_out={protoDir}", str(temp_proto_path)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] Failed to compile proto file: {temp_proto_path} - {result.stderr}")
            return False
        
        print(f"Generated protobuf class for {proto} at {Path(protoDir) / proto}.py")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to generate protobuf class for {proto}: {e}")
        return False
    
def DownloadSchema(dest_dir:str) -> bool:
    try:
        url = "https://raw.githubusercontent.com/google/transit/master/gtfs-realtime/proto/gtfs-realtime.proto"
        outdir = Path(dest_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Downloading protobuf schema from URL: {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(outdir / "gtfs-realtime.proto", "wb") as f:
            f.write(r.content)
        print(f"[DEBUG] Protobuf schema saved: {outdir / 'gtfs-realtime.proto'}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error while downloading protobuf schema: {e} - Status: {e.response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download protobuf schema: {e}")
        return False
        
def run():
    if not CheckProto("gtfs-realtime", "../objects/protos/"):
        DownloadSchema("../objects/protos/")
        if not GenerateProtoClass("gtfs-realtime", "../objects/protos/"):
            print("[ERROR] Failed to generate protobuf class. Exiting.")
            return


if __name__ == "__main__":
    run()