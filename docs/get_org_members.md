# GitHub Organization Member Export

This document describes how to run `src/get_org_members.py`.

## Overview

`src/get_org_members.py` exports organization members to CSV with columns:
- `id`
- `username`
- `role_name`

The script derives `role_name` by listing all members and admin members, then classifying each
member as `admin` or `member`.

## PAT permission required

The script calls this GitHub REST API:
- `GET /orgs/{org}/members` (with role filters `all` and `admin`)

For this operation, token requirements are:
- **Fine-grained PAT**: organization member read permissions.
- **Classic PAT**: `read:org`.

## Supported arguments

Script: `src/get_org_members.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_org_members.py --org-name my-org --output-csv org_members_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_org_members.py --org-name my-org --output-csv org_members_out.csv
```

## Output CSV format

Columns:
- `id`
- `username`
- `role_name`
