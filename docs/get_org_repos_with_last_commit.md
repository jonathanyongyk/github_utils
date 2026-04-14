# GitHub Organization Repository Export with Last Commit

This document describes how to run `src/get_org_repos_with_last_commit.py`.

## Comparison with `get_org_repos.py`

`get_org_repos_with_last_commit.py` is an extended version of `get_org_repos.py`. The core difference is that after fetching the list of repositories from `GET /orgs/{org}/repos`, this script makes **additional API calls** to `GET /repos/{owner}/{repo}/commits` for every repository in order to populate three extra CSV columns:

| Column | Source | How it is derived |
|---|---|---|
| `creator` | Commits API | Login of the author of the **oldest** commit (the commit at the last page of the commit history) |
| `last_commit_author` | Commits API | Login of the author of the **most recent** commit |
| `last_commit_date` | Repos API (`pushed_at`) | Already available from the repo listing response |

`get_org_repos.py` only calls the repos list endpoint and writes five fields (`id`, `name`, `full_name`, `owner/login`, `owner/repos_url`).

### Why was the difference introduced?

The `pushed_at` field returned by the repos listing tells you *when* the last push happened, but it does not tell you *who* made it. Knowing the last commit author is useful for identifying active maintainers or accountability within an org. The `creator` field goes further — by walking to the oldest commit, it approximates who originally bootstrapped each repository, which the repos listing endpoint does not expose at all.

The `last_commit_date` column (sourced from `pushed_at`) gives a rough indicator of whether a repository still has active contributions. A date that is recent suggests ongoing activity, while a date that is months or years in the past may indicate the repository is stale or abandoned — useful for org-wide hygiene audits.

The trade-off is **performance**: for every repository an extra one or two HTTP requests are made to the commits endpoint, so this script is significantly slower on large organizations than `get_org_repos.py`.

## Overview

`src/get_org_repos_with_last_commit.py` lists all repositories in a GitHub organization and exports
selected fields to CSV, including the last commit date, the last commit author, and the repository
creator (the author of the oldest commit).

## PAT permission required

The script calls these GitHub REST APIs:
- `GET /orgs/{org}/repos`
- `GET /repos/{owner}/{repo}/commits`

For this operation, token requirements are:
- **Fine-grained PAT**: repository metadata and contents read permissions.
- **Classic PAT**: `repo` for private repositories, or `public_repo` for public-only repos.

## Supported arguments

Script: `src/get_org_repos_with_last_commit.py`

- `--org-name` (required): GitHub organization name.
- `--output-csv` (required): output CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_org_repos_with_last_commit.py --org-name my-org --output-csv repos_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_org_repos_with_last_commit.py --org-name my-org --output-csv repos_out.csv
```

## Output CSV format

Columns:
- `id`
- `name`
- `full_name`
- `owner/login`
- `owner/repos_url`
- `creator`
- `last_commit_author`
- `last_commit_date`
