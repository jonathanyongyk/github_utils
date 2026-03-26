# GitHub Team Repository Assignment

This document describes how to run `src/assign_team_repos.py`.

## Overview

`src/assign_team_repos.py` assigns repository permissions to teams in bulk from a CSV
file.

For each valid row, the script:
- validates `org_name`, `team_slug`, `repo_name`, and `permission`
- assigns the repository to the team (creates team-repo access if it does not already exist)
- applies the requested repository permission on that team-repo assignment
- records per-row success or failure in the console summary

At the end of the run, it prints success/failure counts and API call totals.

## PAT permission required

The script calls this GitHub REST API:
- `PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}`

For this operation, token requirements are:

- **Fine-grained PAT**: repository **Administration: Read and write** on the target repositories.
- **Classic PAT**:
	- `repo` (required for private repositories)
	- `public_repo` is only sufficient when all target repositories are public.

Additional prerequisites:
- The authenticated user must be allowed to manage team access for target repositories.
- The target team must already exist in the organization.
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/assign_team_repos.py`

- `--input-csv` (required): input CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/assign_team_repos.py --input-csv gh_utils/sample_csv/assign_team_repos.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/assign_team_repos.py --input-csv gh_utils/sample_csv/assign_team_repos.csv
```

## Sample input CSV format

Required columns:
- `org_name`
- `team_slug`
- `repo_name`
- `permission`

`permission` must be one of:
- `pull`
- `triage`
- `push`
- `maintain`
- `admin`

Example:

```csv
org_name,team_slug,repo_name,permission
my-org,backend-devs,repo-one,push
my-org,backend-devs-techleads,repo-one,admin
```

## Output summary

The script prints:
- number of succeeded rows
- number of failed rows
- per-row success/failure details
- API calls successful/failed totals
