#!/usr/bin/env python3
"""Deploy via sshpass+rsync/sftp with ftplib fallback"""
import os, sys, subprocess, pathlib, shutil, ftplib

host     = os.environ["SSH_HOST"]
user     = os.environ["SSH_USER"]
password = os.environ["SSH_PASSWORD"]
remote   = os.environ["SSH_PATH"].rstrip("/")

SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=30"]

SKIP = {".git", ".github", "deploy.py", "deploy-log.txt"}

def get_files():
    local_root = pathlib.Path(".")
    files = []
    for lf in sorted(local_root.rglob("*")):
        if lf.is_dir(): continue
        parts = lf.parts
        if any(p in SKIP or p.startswith(".") for p in parts): continue
        files.append(lf)
    return files

print(f"=== Deploying to {user}@{host}:{remote} ===")

# --- Attempt 1: SSH (test connection) ---
print("\n[1] Testing SSH connection...")
test_cmd = ["sshpass", "-p", password, "ssh"] + SSH_OPTS + [
    f"{user}@{host}", "echo SSH_OK"
]
r = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
ssh_ok = r.returncode == 0 and "SSH_OK" in r.stdout
print(f"  SSH test: {'OK' if ssh_ok else 'FAILED'}")
if not ssh_ok:
    print(f"  stdout: {r.stdout.strip()}")
    print(f"  stderr: {r.stderr.strip()}")

if ssh_ok:
    # --- Attempt 2: rsync over SSH ---
    print("\n[2] Trying rsync...")
    rsync_cmd = [
        "sshpass", "-p", password,
        "rsync", "-avz", "--delete",
        "--exclude=.git", "--exclude=.github",
        "--exclude=deploy.py", "--exclude=deploy-log.txt",
        "-e", f"ssh {' '.join(SSH_OPTS)}",
        "./",
        f"{user}@{host}:{remote}/"
    ]
    r2 = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=120)
    print(f"  rsync RC: {r2.returncode}")
    if r2.stdout: print("  stdout:", r2.stdout[-1000:])
    if r2.stderr: print("  stderr:", r2.stderr[-500:])
    if r2.returncode == 0:
        print("\n✓ rsync deployment succeeded!")
        sys.exit(0)
    
    # --- Attempt 3: sftp batch ---
    print("\n[3] Trying sftp batch upload...")
    files = get_files()
    dirs_seen = set()
    sftp_cmds = []
    for lf in files:
        rel_dir = str(lf.parent)
        if rel_dir != "." and rel_dir not in dirs_seen:
            sftp_cmds.append(f"-mkdir {remote}/{rel_dir}")
            dirs_seen.add(rel_dir)
    for lf in files:
        sftp_cmds.append(f"put {lf} {remote}/{lf}")
    sftp_cmds.append("bye")
    batch = "\n".join(sftp_cmds)
    
    sftp_cmd = ["sshpass", "-p", password, "sftp"] + SSH_OPTS + [f"{user}@{host}"]
    r3 = subprocess.run(sftp_cmd, input=batch.encode(), capture_output=True, timeout=120)
    print(f"  sftp RC: {r3.returncode}")
    if r3.stdout: print("  stdout:", r3.stdout.decode()[-1000:])
    if r3.stderr: print("  stderr:", r3.stderr.decode()[-500:])
    if r3.returncode == 0:
        print(f"\n✓ sftp batch upload succeeded! {len(files)} files.")
        sys.exit(0)

# --- Attempt 4: FTP fallback ---
print("\n[4] Trying FTP (port 21)...")
# FTP path: strip leading slash, use relative from FTP root
# Beget FTP root is typically /home/user/ or chrooted to home
ftp_remote = remote.lstrip("/")  # e.g. "pravo-trans.ru/public_html"

try:
    ftp = ftplib.FTP()
    ftp.connect(host, 21, timeout=30)
    print(f"  FTP connected to {host}:21")
    ftp.login(user, password)
    print(f"  FTP login OK as {user}")
    ftp.set_pasv(True)
    
    # Try to navigate to remote path
    try:
        ftp.cwd(remote)
        print(f"  cwd to {remote}: OK")
    except ftplib.error_perm:
        try:
            ftp.cwd(ftp_remote)
            print(f"  cwd to {ftp_remote}: OK")
        except ftplib.error_perm as e:
            print(f"  ERROR: Cannot cd to path: {e}")
            # Print FTP directory listing to debug
            print("  FTP root listing:")
            ftp.retrlines("LIST", print)
            ftp.quit()
            sys.exit(1)
    
    def ftp_mkdir_p(ftp_conn, path):
        parts = [p for p in path.split("/") if p]
        for i in range(len(parts)):
            d = "/".join(parts[:i+1])
            try: ftp_conn.mkd(d)
            except: pass
    
    files = get_files()
    uploaded = 0
    for lf in files:
        rel = str(lf)
        rel_dir = str(lf.parent)
        if rel_dir != ".":
            ftp_mkdir_p(ftp, rel_dir)
        with open(lf, "rb") as f:
            try:
                ftp.storbinary(f"STOR {rel}", f)
                print(f"  -> {rel}")
                uploaded += 1
            except Exception as e:
                print(f"  FAIL {rel}: {e}")
    
    ftp.quit()
    print(f"\n✓ FTP deployment succeeded! {uploaded} files.")
    sys.exit(0)

except Exception as e:
    print(f"  FTP ERROR: {e}")
    import traceback; traceback.print_exc()

print("\n✗ All deployment methods failed.")
sys.exit(1)
