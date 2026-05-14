#!/usr/bin/env python3
"""
collect_dd_serials_rest.py
Collects HDD serial numbers from Data Domain appliances via the REST API.
Outputs: dd_serials_<timestamp>.csv
"""

import requests
import csv
import os
import sys
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INVENTORY_FILE = os.environ.get("DD_INVENTORY", "dd_inventory.txt")
DD_REST_USER   = os.environ.get("DD_REST_USER", "sysadmin")
DD_REST_PASS   = os.environ.get("DD_REST_PASS", "")
DD_REST_PORT   = os.environ.get("DD_REST_PORT", "3009")
VERIFY_SSL     = os.environ.get("DD_VERIFY_SSL", "false").lower() == "true"
OUTPUT_DIR     = os.environ.get("OUTPUT_DIR", "artifacts")
TIMESTAMP      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE    = os.path.join(OUTPUT_DIR, f"dd_serials_{TIMESTAMP}.csv")

def load_inventory(path):
    hosts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line)
    return hosts

def get_auth_token(session, base_url):
    resp = session.post(
        f"{base_url}/rest/v1.0/auth",
        json={"username": DD_REST_USER, "password": DD_REST_PASS},
        verify=VERIFY_SSL,
        timeout=30
    )
    resp.raise_for_status()
    return resp.headers.get("X-DD-AUTH-TOKEN") or resp.json().get("token")

def get_disks(session, base_url, token):
    headers = {"X-DD-AUTH-TOKEN": token, "Accept": "application/json"}
    resp = session.get(
        f"{base_url}/rest/v1.0/dd-systems/0/storage/disks",
        headers=headers,
        verify=VERIFY_SSL,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

def parse_disk_response(host, data):
    rows = []
    disks = data.get("disk", data.get("disks", []))
    if isinstance(disks, dict):
        disks = disks.get("disk", [])
    for disk in disks:
        rows.append({
            "hostname":     host,
            "disk_id":      disk.get("location", disk.get("id", "unknown")),
            "status":       disk.get("state", disk.get("status", "unknown")),
            "model":        disk.get("model", "unknown"),
            "serial":       disk.get("serial_no", disk.get("serial_number", "unknown")),
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
        print(f"[*] Querying REST API on {host} ...")
        base_url = f"https://{host}:{DD_REST_PORT}"
        session  = requests.Session()
        try:
            token = get_auth_token(session, base_url)
            data  = get_disks(session, base_url, token)
            rows  = parse_disk_response(host, data)
            print(f"  [OK]   {host}: {len(rows)} disk(s) found")
            all_rows.extend(rows)
        except Exception as e:
            print(f"  [FAIL] {host}: {e}", file=sys.stderr)
            errors.append(host)
        finally:
            session.close()

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