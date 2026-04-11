#!/usr/bin/env python3
"""Deploy via sftp, auto-discovering the correct remote path"""
import os, sys, subprocess, pathlib

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]
remote   = os.environ["SSH_PATH"].rstrip("/")

SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=30"]
SKIP = {".git", ".github", "deploy.py", "deploy-log.txt"}

def ssh_run(cmd_str):
    r = subprocess.run(
        ["sshpass", "-p", password, "ssh"] + SSH_OPTS + [f"{user}@{host}", cmd_str],
        capture_output=True, text=True, timeout=30
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def sftp_run(batch):
    r = subprocess.run(
        ["sshpass", "-p", password, "sftp"] + SSH_OPTS + [f"{user}@{host}"],
        input=batch.encode(), capture_output=True, timeout=180
    )
    return r.returncode, r.stdout.decode(), r.stderr.decode()

def get_files():
    files = []
    for lf in sorted(pathlib.Path(".").rglob("*")):
        if lf.is_dir(): continue
        parts = lf.parts
        if any(p in SKIP or p.startswith(".") for p in parts): continue
        files.append(lf)
    return files

print(f"=== Deploying to {user}@{host} ===")
print(f"    SSH_PATH hint: {remote}")

# --- Step 1: Test SSH ---
rc, out, err = ssh_run("echo SSH_OK")
if rc != 0 or "SSH_OK" not in out:
    print(f"SSH FAILED: {err}")
    sys.exit(1)
print("SSH: OK")

# --- Step 2: Discover real remote path ---
print("\n[Discovering remote path...]")
rc, out, err = ssh_run(f"pwd && echo '---' && ls ~ && echo '---' && find ~ -maxdepth 4 -name public_html 2>/dev/null | head -5")
print(out)

# Try to find public_html path
lines = out.splitlines()
home = lines[0] if lines else ""
found_paths = [l.strip() for l in lines if "public_html" in l]
print(f"Home dir: {home}")
print(f"Found public_html paths: {found_paths}")

# Determine actual remote path
actual_remote = None
if found_paths:
    actual_remote = found_paths[0]
    print(f"Using discovered path: {actual_remote}")
else:
    # Try variations
    for candidate in [
        remote,
        f"{home}/{remote.lstrip('/')}",
        f"{home}/pravo-trans.ru/public_html",
        f"{home}/www",
        f"{home}/public_html",
    ]:
        rc2, out2, _ = ssh_run(f"test -d '{candidate}' && echo EXISTS || echo MISSING")
        print(f"  {candidate}: {out2.strip()}")
        if "EXISTS" in out2:
            actual_remote = candidate
            break

if not actual_remote:
    print(f"\nERROR: Cannot find web root. Please check SSH_PATH secret.")
    print("Listing home directory:")
    rc, out, _ = ssh_run("ls -la ~")
    print(out)
    sys.exit(1)

print(f"\nUsing remote path: {actual_remote}")

# --- Step 3: Upload via sftp ---
files = get_files()
dirs_seen = set()
cmds = []

for lf in files:
    rel_dir = str(lf.parent)
    if rel_dir != "." and rel_dir not in dirs_seen:
        cmds.append(f"-mkdir {actual_remote}/{rel_dir}")
        dirs_seen.add(rel_dir)

for lf in files:
    cmds.append(f"put {lf} {actual_remote}/{lf}")

cmds.append("bye")
batch = "\n".join(cmds)

print(f"\n[Uploading {len(files)} files via sftp...]")
rc, stdout, stderr = sftp_run(batch)
print("STDOUT:", stdout[-2000:] if len(stdout) > 2000 else stdout)
if stderr.strip():
    # Filter out known harmless messages
    errs = [l for l in stderr.splitlines() if l.strip() and "known hosts" not in l and "BeGet" not in l and "Warning" not in l]
    if errs:
        print("STDERR:", "\n".join(errs[:20]))

# Verify upload by checking a key file
rc2, out2, _ = ssh_run(f"ls -la '{actual_remote}/index.html' 2>&1")
print(f"\nVerify index.html: {out2.strip()}")

if "index.html" in out2 and "No such" not in out2:
    print(f"\n✓ Deployment succeeded! {len(files)} files uploaded to {actual_remote}")
    sys.exit(0)
else:
    print(f"\n✗ Upload verification failed.")
    sys.exit(1)
