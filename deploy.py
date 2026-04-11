#!/usr/bin/env python3
import os, sys, paramiko, pathlib

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]
remote   = os.environ["SSH_PATH"].rstrip("/")

SKIP = {".git", ".github", "deploy.py"}

transport = paramiko.Transport((host, 22))
transport.connect(username=user, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)

def ensure_dir(path):
    try: sftp.stat(path)
    except FileNotFoundError:
        parts = path.split("/")
        for i in range(2, len(parts)+1):
            d = "/".join(parts[:i])
            try: sftp.stat(d)
            except FileNotFoundError:
                try: sftp.mkdir(d)
                except: pass

local_root = pathlib.Path(".")
uploaded = 0
for local_file in sorted(local_root.rglob("*")):
    if local_file.is_dir(): continue
    parts = local_file.parts
    if any(p in SKIP or p.startswith(".") for p in parts): continue
    rel = str(local_file)
    remote_path = f"{remote}/{rel}"
    remote_dir = remote_path.rsplit("/", 1)[0]
    ensure_dir(remote_dir)
    print(f"  -> {rel}")
    sftp.put(str(local_file), remote_path)
    uploaded += 1

sftp.close(); transport.close()
print(f"\nDone: {uploaded} files uploaded to {host}:{remote}")
