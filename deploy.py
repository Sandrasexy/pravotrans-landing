#!/usr/bin/env python3
"""Deploy files to Beget via sftp — uploads to SSH home dir (= site root)"""
import os, sys, subprocess, pathlib

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]

SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=30"]
SKIP = {".git", ".github", "deploy.py", "deploy-log.txt"}

def get_files():
    files = []
    for lf in sorted(pathlib.Path(".").rglob("*")):
        if lf.is_dir(): continue
        parts = lf.parts
        if any(p in SKIP or p.startswith(".") for p in parts): continue
        files.append(lf)
    return files

print(f"=== Deploying to {user}@{host} (site root) ===")

# Test SSH
r = subprocess.run(
    ["sshpass", "-p", password, "ssh"] + SSH_OPTS + [f"{user}@{host}", "echo SSH_OK; pwd"],
    capture_output=True, text=True, timeout=30
)
if r.returncode != 0 or "SSH_OK" not in r.stdout:
    print(f"SSH FAILED: {r.stderr}")
    sys.exit(1)
remote_root = r.stdout.splitlines()[1] if len(r.stdout.splitlines()) > 1 else "~"
print(f"SSH OK — remote root: {remote_root}")

# Build sftp batch: upload to home dir (site root)
files = get_files()
dirs_seen = set()
cmds = []

for lf in files:
    rel_dir = str(lf.parent)
    if rel_dir != "." and rel_dir not in dirs_seen:
        cmds.append(f"-mkdir {rel_dir}")
        dirs_seen.add(rel_dir)

for lf in files:
    cmds.append(f"put {lf} {lf}")

cmds.append("bye")
batch = "\n".join(cmds)

print(f"\nUploading {len(files)} files...")
r2 = subprocess.run(
    ["sshpass", "-p", password, "sftp"] + SSH_OPTS + [f"{user}@{host}"],
    input=batch.encode(), capture_output=True, timeout=180
)
if r2.stdout:
    print(r2.stdout.decode()[-2000:])

# Verify
r3 = subprocess.run(
    ["sshpass", "-p", password, "ssh"] + SSH_OPTS + [f"{user}@{host}", "ls -la index.html 2>&1"],
    capture_output=True, text=True, timeout=15
)
print(f"\nVerify: {r3.stdout.strip()}")

if r3.returncode == 0 and "index.html" in r3.stdout:
    print(f"\n✓ Done: {len(files)} files deployed to {remote_root}")
    sys.exit(0)
else:
    print("\n✗ Verification failed")
    sys.exit(1)
