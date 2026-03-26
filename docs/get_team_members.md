# GitHub Team Member Export

This document describes how to run `src/get_team_members.py`.

## Overview

`src/get_team_members.py` lists all teams in a GitHub organization and the members of each team.
Exports results to CSV.

For each team, the script:
- retrieves all members of the team (including members from child teams)
- records per-team success or failure in the console summary

At the end of the run, it prints success/failure counts and total rows written.

**Note:** Members listed include those inherited from child teams. The GitHub REST API does not provide a parameter to exclude members from child teams, so the script retrieves all members as returned by the API. If you need only direct members, filter the output accordingly.

## PAT permission required

The script calls these GitHub REST APIs:
- `GET /orgs/{org}/teams`
- `GET /orgs/{org}/teams/{team_slug}` (only when `--team-slug` is provided)
- `GET /orgs/{org}/teams/{team_slug}/members`

For these operations, token requirements are:
- **Fine-grained PAT**: organization/team read permissions and organization member read permissions.
- **Classic PAT**: `read:org`.

Additional prerequisites:
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/get_team_members.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--team-slug` (optional): team slug. If provided, export members for this team only.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_team_members.py --org-name my-org --output-csv team_members_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_team_members.py --org-name my-org --output-csv team_members_out.csv
```

Filter to a single team:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_team_members.py --org-name my-org --team-slug backend-devs --output-csv team_members_out.csv
```

## Output CSV format

Columns:
- `team_id`
- `team_name`
- `team_slug`
- `login`
