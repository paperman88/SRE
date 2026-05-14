# Data Domain HDD Serial Number Collection

**Platform:** Semaphore CI/CD
**Target Systems:** Dell EMC Data Domain Appliances
**Output:** Timestamped CSV with hostname, disk location, and serial number

## Repo Structure

```
SRE/
â”œâ”€â”€ dd_inventory.txt                      # List of Data Domain hosts
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ collect_dd_serials_ssh.py         # SSH-based collection
â”‚   â””â”€â”€ collect_dd_serials_rest.py        # REST API-based collection
â””â”€â”€ .semaphore/
    â””â”€â”€ dd_serial_collection.yml          # Semaphore pipeline definition
```

## Quick Start

1. Edit `dd_inventory.txt` â€” add your Data Domain hostnames/IPs
2. Add Semaphore secrets: `dd-credentials` and `dd-ssh-key`
3. Trigger the pipeline in Semaphore
4. Download the merged CSV from the Artifacts tab

## Output CSV Columns

| Column | Description |
|---|---|
| `hostname` | Data Domain FQDN or IP |
| `disk_id` | Disk slot / location |
| `status` | Disk status (In Use, Spare, Failed) |
| `model` | Drive model number |
| `serial` | HDD serial number |
| `collected_at` | UTC timestamp of collection |
| `source` | Collection method: `ssh` or `rest` |

## Semaphore Secrets Required

| Secret Name | Keys |
|---|---|
| `dd-credentials` | `DD_SSH_USER`, `DD_SSH_PASS`, `DD_REST_USER`, `DD_REST_PASS` |
| `dd-ssh-key` | `DD_SSH_KEY_DATA` |

*Maintained by the Infrastructure / SRE Team.*