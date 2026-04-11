#!/usr/bin/env python3
"""Deploy via sshpass+rsync with fallback to sshpass+sftp batch"""
import os, sys, subprocess, pathlib, shutil

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]
remote   = os.environ["SSH_PATH"].rstrip("/")

SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=30"]

print(f"=== Deploying to {user}@{host}:{remote} ===")

# --- Step 1: Test SSH connection and verify remote path ---
print("\n[1] Testing SSH connection and remote path...")
test_cmd = ["sshpass", "-p", password, "ssh"] + SSH_OPTS + [
    f"{user}@{host}",
    f"ls -la '{remote}' 2>&1 || (echo 'PATH_MISSING'; find /home -maxdepth 5 -name public_html 2>/dev/null | head -5; ls ~ 2>/dev/null)"
]
r = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
print("STDOUT:", r.stdout.strip())
if r.stderr.strip():
    print("STDERR:", r.stderr.strip())
print("RC:", r.returncode)

if r.returncode != 0:
    print("SSH connection FAILED. Cannot deploy.")
    sys.exit(1)

if "PATH_MISSING" in r.stdout:
    print(f"\nERROR: Remote path '{remote}' does not exist!")
    print("Please check SSH_PATH secret value.")
    sys.exit(1)

# --- Step 2: Try rsync ---
print("\n[2] Attempting rsync deployment...")
if shutil.which("rsync"):
    rsync_cmd = [
        "sshpass", "-p", password,
        "rsync", "-avz", "--delete",
        "--exclude=.git", "--exclude=.github", "--exclude=deploy.py",
        "-e", f"ssh {' '.join(SSH_OPTS)}",
        "./",
        f"{user}@{host}:{remote}/"
    ]
    r2 = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=120)
    print("STDOUT:", r2.stdout[-3000:] if len(r2.stdout) > 3000 else r2.stdout)
    if r2.stderr.strip():
        print("STDERR:", r2.stderr.strip())
    print("RC:", r2.returncode)

    if r2.returncode == 0:
        print("\n✓ rsync deployment succeeded!")
        sys.exit(0)
    else:
        print("\nrsync failed, falling back to sftp batch upload...")
else:
    print("rsync not found, using sftp batch upload...")

# --- Step 3: Fallback — sftp batch upload ---
print("\n[3] Building file list for sftp batch upload...")
SKIP = {".git", ".github", "deploy.py"}
local_root = pathlib.Path(".")
sftp_cmds = [f"cd {remote}"]

uploaded_files = []
for local_file in sorted(local_root.rglob("*")):
    if local_file.is_dir():
        continue
    parts = local_file.parts
    if any(p in SKIP or p.startswith(".") for p in parts):
        continue
    uploaded_files.append(local_file)

# Create dirs first
dirs_seen = set()
for lf in uploaded_files:
    rel_dir = str(lf.parent)
    if rel_dir != "." and rel_dir not in dirs_seen:
        sftp_cmds.append(f"-mkdir {remote}/{rel_dir}")
        dirs_seen.add(rel_dir)

for lf in uploaded_files:
    sftp_cmds.append(f"put {lf} {remote}/{lf}")

sftp_cmds.append("bye")
batch = "\n".join(sftp_cmds)

print(f"  Will upload {len(uploaded_files)} files")

sftp_cmd = ["sshpass", "-p", password, "sftp"] + SSH_OPTS + [f"{user}@{host}"]
r3 = subprocess.run(sftp_cmd, input=batch.encode(), capture_output=True, timeout=120)
print("STDOUT:", r3.stdout.decode()[-2000:])
if r3.stderr:
    print("STDERR:", r3.stderr.decode()[-1000:])
print("RC:", r3.returncode)

if r3.returncode == 0:
    print(f"\n✓ sftp batch upload succeeded! {len(uploaded_files)} files.")
    sys.exit(0)
else:
    print("\nsftp batch upload also failed.")
    sys.exit(1)
