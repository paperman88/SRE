#!/usr/bin/env python3
"""
collect_dd_serials_ssh.py
Collects HDD serial numbers from Data Domain appliances via SSH.
Outputs: dd_serials_<timestamp>.csv
"""

import subprocess
import csv
import os
import re
import sys
from datetime import datetime

INVENTORY_FILE = os.environ.get("DD_INVENTORY", "dd_inventory.txt")
SSH_USER       = os.environ.get("DD_SSH_USER", "sysadmin")
SSH_PASS       = os.environ.get("DD_SSH_PASS", "")
SSH_KEY        = os.environ.get("DD_SSH_KEY", "")
SSH_PORT       = os.environ.get("DD_SSH_PORT", "22")
OUTPUT_DIR     = os.environ.get("OUTPUT_DIR", "artifacts")
TIMESTAMP      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE    = os.path.join(OUTPUT_DIR, f"dd_serials_{TIMESTAMP}.csv")

DISK_LINE_RE = re.compile(
    r"^\s*(\S+)\s+(In Use|Spare|Failed|Absent|Unknown)\s+(\S+)\s+(\S+)\s+", re.IGNORECASE
)

def load_inventory(path):
    hosts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line)
    return hosts

def run_ssh_command(host, command):
    if SSH_KEY:
        cmd = [
            "ssh", "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=15",
            "-p", SSH_PORT,
            f"{SSH_USER}@{host}",
            command
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    elif SSH_PASS:
        cmd = [
            "sshpass", "-e",
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=15",
            "-p", SSH_PORT,
            f"{SSH_USER}@{host}",
            command
        ]
        env = os.environ.copy()
        env["SSHPASS"] = SSH_PASS
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    else:
        print(f"  [ERROR] No SSH key or password configured for {host}", file=sys.stderr)
        return "", "No credentials", 1
    return result.stdout, result.stderr, result.returncode

def parse_disk_output(host, raw_output):
    rows = []
    for line in raw_output.splitlines():
        m = DISK_LINE_RE.match(line)
        if m:
            rows.append({
                "hostname":     host,
                "disk_id":      m.group(1),
                "status":       m.group(2),
                "model":        m.group(3),
                "serial":       m.group(4),
                "collected_at": TIMESTAMP,
            })
    return rows

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    hosts = load_inventory(INVENTORY_FILE)
    if not hosts:
        print("No hosts found in inventory. Exiting.", file=sys.stderr)
        sys.exit(1)

    all_rows, errors = [], []
    for host in hosts:
        print(f"[*] Connecting to {host} ...")
        stdout, stderr, rc = run_ssh_command(host, "disk show hardware")
        if rc != 0:
            print(f"  [FAIL] {host}: {stderr.strip()}", file=sys.stderr)
            errors.append(host)
            continue
        rows = parse_disk_output(host, stdout)
        print(f"  [OK]   {host}: {len(rows)} disk(s) found")
        all_rows.extend(rows)

    fieldnames = ["hostname", "disk_id", "status", "model", "serial", "collected_at"]
    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n[+] Output saved to: {OUTPUT_FILE}")
    print(f"[+] Total disks collected: {len(all_rows)}")
    if errors:
        print(f"[!] Failed hosts ({len(errors)}): {', '.join(errors)}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()