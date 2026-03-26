# GitHub Organization Repository Export

This document describes how to run `src/get_org_repos.py`.

## Overview

`src/get_org_repos.py` lists all repositories in a GitHub organization and exports selected
fields to CSV.

## PAT permission required

The script calls this GitHub REST API:
- `GET /orgs/{org}/repos`

For this operation, token requirements are:
- **Fine-grained PAT**: repository metadata read permissions.
- **Classic PAT**: `repo` for private repositories, or `public_repo` for public-only repos.

## Supported arguments

Script: `src/get_org_repos.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_org_repos.py --org-name my-org --output-csv repos_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_org_repos.py --org-name my-org --output-csv repos_out.csv
```

## Output CSV format

Columns:
- `id`
- `name`
- `full_name`
- `owner/login`
- `owner/repos_url`
