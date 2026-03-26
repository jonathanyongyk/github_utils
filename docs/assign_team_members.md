# GitHub Team Member Assignment

This document describes how to run `src/assign_team_members.py`.

## Overview

`src/assign_team_members.py` assigns users to GitHub teams in bulk from a CSV file.

For each valid row, the script:
- validates `org_name`, `team_slug`, `username`, and `role`
- applies team membership with role `member` or `maintainer`
- records per-row success or failure in the console summary

At the end of the run, it prints success/failure counts and API call totals.

## PAT permission required

The script calls this GitHub REST API:
- `PUT /orgs/{org}/teams/{team_slug}/memberships/{username}`

For this operation, token requirements are:

- **Fine-grained PAT**: organization/team administration permissions that allow team membership updates.
- **Classic PAT**: `admin:org` (team membership management).

Additional prerequisites:
- The target team must already exist.
- The target user must exist in the enterprise/org and be eligible for assignment.
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/assign_team_members.py`

- `--input-csv` (required): input CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/assign_team_members.py --input-csv gh_utils/sample_csv/assign_team_members.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/assign_team_members.py --input-csv gh_utils/sample_csv/assign_team_members.csv
```

## Sample input CSV format

Required columns:
- `org_name`
- `team_slug`
- `username`
- `role`

`role` must be one of:
- `member`
- `maintainer`

Example:

```csv
org_name,team_slug,username,role
my-org,backend-devs,alice,member
my-org,backend-devs-techleads,carol,maintainer
```

## Output summary

The script prints:
- number of succeeded rows
- number of failed rows
- per-row success/failure details
- API calls successful/failed totals
