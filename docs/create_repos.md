## GitHub Repo Creation (CSV)

This document describes how to run `src/create_repos.py`.

## Overview

`src/create_repos.py` creates private, empty repositories from a CSV file and then assigns
an admin collaborator for each created repository.

For each valid row, the script:
- creates the repository in the target organization
- assigns the specified `repo_admin` as repository admin
- records successful repository name and URL to the output CSV

At the end of the run, it prints a success/failure summary to the console.

## PAT permission required

The script calls these GitHub REST APIs:
- `POST /orgs/{org}/repos` (create organization repository)
- `PUT /repos/{owner}/{repo}/collaborators/{username}` (assign repo admin collaborator)

For these operations, token requirements are:

- **Fine-grained PAT**: repository **Administration: Read and write** on target repositories/org.
- **Classic PAT**:
	- `repo` (required for private repositories)
	- `public_repo` is only sufficient when all target repositories are public.

Additional prerequisites:
- The authenticated user must be allowed to create repositories in the target organization.
- The authenticated user must have rights to manage collaborators on created repositories.
- If SSO/SAML is enforced, authorize the token for the organization.

## Supported arguments

Script: `src/create_repos.py`

- `--input-csv` (required): input CSV file path.
- `--output-csv` (required): output CSV path for successfully created repositories.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/create_repos.py --input-csv gh_utils/sample_csv/repos.csv --output-csv gh_utils/sample_csv/created_repos.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/create_repos.py --input-csv gh_utils/sample_csv/repos.csv --output-csv gh_utils/sample_csv/created_repos.csv
```

## Sample input CSV format

Required columns:
- `organization`
- `repo_name`
- `repo_description`
- `repo_admin`

Example:

```csv
organization,repo_name,repo_description,repo_admin
my-org,repo-one,first repo,alice
my-org,repo-two,second repo,bob
```

## Output CSV format

The output CSV (`--output-csv`) contains successful rows with:
- `repo_name`
- `repo_url`
