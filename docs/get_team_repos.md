# GitHub Team Repository Export

This document describes how to run `src/get_team_repos.py`.

## Overview

`src/get_team_repos.py` lists all teams in a GitHub organization and the repositories accessible
to each team, including the team's permission on each repository. Exports results to CSV.

For each team, the script:
- retrieves all repositories accessible to the team
- resolves the team's permission level on each repository
- records per-team success or failure in the console summary

At the end of the run, it prints success/failure counts and total rows written.

## PAT permission required

The script calls these GitHub REST APIs:
- `GET /orgs/{org}/teams`
- `GET /orgs/{org}/teams/{team_slug}` (only when `--team-slug` is provided)
- `GET /orgs/{org}/teams/{team_slug}/repos`

For these operations, token requirements are:
- **Fine-grained PAT**: organization/team read permissions and repository metadata read permissions.
- **Classic PAT**: `read:org` and `repo` (or `public_repo` for public-only repositories).

Additional prerequisites:
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/get_team_repos.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--team-slug` (optional): team slug. If provided, export repos for this team only.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_team_repos.py --org-name my-org --output-csv team_repos_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_team_repos.py --org-name my-org --output-csv team_repos_out.csv
```

Filter to a single team:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_team_repos.py --org-name my-org --team-slug backend-devs --output-csv team_repos_out.csv
```

## Output CSV format

Columns:
- `team_id`
- `team_name`
- `team_slug`
- `repo_id`
- `repo_name`
- `permission`
- `repo_url`
