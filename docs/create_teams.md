# GitHub Team Creation

This document describes how to run `src/create_teams.py`.

## Overview

`src/create_teams.py` creates organization teams from a CSV file and supports nested
team creation via the optional `parent_team` column.

For each valid row, the script:
- validates team data (`org_name`, `team_name`, `privacy`, `parent_team`)
- resolves parent team ID only when `parent_team` is provided
- creates the team in GitHub
- writes successful team records to the output CSV

At the end of the run, it prints a success/failure summary to the console.

## PAT permission required

The script calls these GitHub REST APIs:
- `POST /orgs/{org}/teams`
- `GET /orgs/{org}/teams/{team_slug}` (only when `parent_team` is provided and parent id is not in local cache)

For these operations, token requirements are:

- **Fine-grained PAT**: organization/team administration permissions that allow team creation and team lookup in the target organization.
- **Classic PAT**: `admin:org` (team management operations).

Additional prerequisites:
- The authenticated user must be allowed to create/manage teams in the target organization.
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/create_teams.py`

- `--input-csv` (required): input CSV file path.
- `--output-csv` (required): output CSV for successfully created teams.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/create_teams.py --input-csv gh_utils/sample_csv/teams.csv --output-csv teams_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/create_teams.py --input-csv gh_utils/sample_csv/teams.csv --output-csv teams_out.csv
```

## Sample input CSV format

Required columns:
- `org_name`
- `team_name`
- `privacy` (`closed` or `secret`)
- `parent_team` (can be empty)

Example:

```csv
org_name,team_name,privacy,parent_team
my-org,backend-devs,closed,
my-org,backend-devs-techleads,closed,backend-devs
```

## Output CSV format

The output CSV (`--output-csv`) contains successful rows with:
- `team_id`
- `org_name`
- `team_name`
- `team_slug`

## Notes

- `parent_team` is resolved on demand by team name.
- Parent team lookup uses in-memory caching to reduce repeated network calls in the same run.
- The script prints success/failure summary to console.
