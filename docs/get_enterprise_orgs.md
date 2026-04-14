# GitHub Enterprise Organization Export

This document describes how to run `src/get_enterprise_orgs.py`.

## Overview

`src/get_enterprise_orgs.py` lists all organizations in a GitHub Enterprise account and exports
selected fields to CSV.

## Why GraphQL instead of REST

The GitHub REST API does not provide an endpoint to list organizations within a GitHub Enterprise Cloud account on `api.github.com`. The REST enterprise-admin organization endpoints (`/admin/organizations`) only exist on **GitHub Enterprise Server** (self-hosted instances) and only support creating or renaming organizations — not listing them.

The GraphQL API is the only supported way to enumerate all organizations under a GitHub Enterprise Cloud account, via the `enterprise(slug:)` query.

## PAT permission required

The script calls the GitHub GraphQL API:
- `POST /graphql` (enterprise organizations query)

For this operation, token requirements are:
- **Classic PAT**: `read:enterprise` scope.

> **Note:** Fine-grained personal access tokens do not support enterprise-level scope and cannot be used with this script.

## Supported arguments

Script: `src/get_enterprise_orgs.py`

- `--enterprise` (required): GitHub Enterprise slug (the short name used in URLs).
- `--output-csv` (required): output CSV file path.
- `--token` (optional): GitHub token. If omitted, `GITHUB_TOKEN` is used.

## Example calls

Pass token via argument:

```powershell
python src/get_enterprise_orgs.py --enterprise my-enterprise --output-csv orgs_out.csv --token <YOUR_GITHUB_TOKEN>
```

Use `GITHUB_TOKEN` environment variable:

```powershell
$env:GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"
python src/get_enterprise_orgs.py --enterprise my-enterprise --output-csv orgs_out.csv
```

## Output CSV format

Columns:
- `id`
- `login`
- `name`
- `url`
- `description`
