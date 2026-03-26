# GitHub Organization User Assignment

This document describes how to run `src/assign_org_users.py`.

## Overview

`src/assign_org_users.py` assigns EMU users to a GitHub organization from a CSV file.

For each valid row, the script:
- validates `org_name`, `username`, and `role_name`
- assigns the user to the organization via organization membership API
- records per-row success or failure in the console summary

At the end of the run, it prints success/failure counts and API call totals.

## PAT permission required

The script calls this GitHub REST API:
- `PUT /orgs/{org}/memberships/{username}`

For this operation, token requirements are:
- **Fine-grained PAT**: organization member administration permissions for the target org.
- **Classic PAT**: `admin:org`.

Additional prerequisites:
- User must exist as an EMU account.
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/assign_org_users.py`

- `--input-csv` (required): input CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/assign_org_users.py --input-csv org_user_assignment.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/assign_org_users.py --input-csv org_user_assignment.csv
```

## Sample input CSV format

Required columns:
- `org_name`
- `username`
- `role_name`

`role_name` must be one of:
- `member`
- `admin`

Example:

```csv
org_name,username,role_name
my-org,alice,member
my-org,bob,admin
```

## Output summary

The script prints:
- number of succeeded rows
- number of failed rows
- per-row success/failure details
- API calls successful/failed totals
