#!/usr/bin/env python3
import os, sys, pathlib, traceback

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]
remote   = os.environ["SSH_PATH"].rstrip("/")

print(f"Connecting to {user}@{host}:22 ...")
print(f"Remote path: {remote}")

try:
    import paramiko
except ImportError:
    print("ERROR: paramiko not installed"); sys.exit(1)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(
        hostname=host, port=22,
        username=user, password=password,
        allow_agent=False, look_for_keys=False,
        timeout=30, banner_timeout=30, auth_timeout=30
    )
    print("SSH connected OK")
except Exception as e:
    print(f"SSH CONNECT FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Verify remote path exists
stdin, stdout, stderr = client.exec_command(f"ls -la {remote} 2>&1 || echo NOTFOUND")
out = stdout.read().decode().strip()
print(f"Remote ls: {out}")
if "NOTFOUND" in out or "No such file" in out:
    print(f"ERROR: Remote path {remote!r} does not exist. Trying to find the right path...")
    stdin, stdout, stderr = client.exec_command("find /home -maxdepth 5 -name 'public_html' 2>/dev/null | head -5; echo ---; ls /home/ 2>/dev/null; echo ---; pwd")
    out2 = stdout.read().decode().strip()
    print(f"Discovery: {out2}")
    sys.exit(1)

sftp = client.open_sftp()

SKIP = {".git", ".github", "deploy.py"}

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
    try:
        sftp.put(str(local_file), remote_path)
        print(f"  -> {rel}")
        uploaded += 1
    except Exception as e:
        print(f"  FAIL {rel}: {e}")

sftp.close()
client.close()
print(f"\nDone: {uploaded} files uploaded to {host}:{remote}")
