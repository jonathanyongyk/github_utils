# GitHub Organization Team Export

This document describes how to run `src/get_org_teams.py`.

## Overview

`src/get_org_teams.py` lists all teams in a GitHub organization and exports selected
fields to CSV.

## PAT permission required

The script calls this GitHub REST API:
- `GET /orgs/{org}/teams`

For this operation, token requirements are:
- **Fine-grained PAT**: organization/team read permissions.
- **Classic PAT**: `read:org`.

## Supported arguments

Script: `src/get_org_teams.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_org_teams.py --org-name my-org --output-csv teams_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_org_teams.py --org-name my-org --output-csv teams_out.csv
```

## Output CSV format

Columns:
- `id`
- `org_name`
- `team_name`
- `team_slug`
- `privacy`
- `parent`
- `parent_team_slug`
