import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def list_org_repositories(token: str, org_name: str) -> List[Dict[str, Any]]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    repos: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while True:
        url = (
            f"https://api.github.com/orgs/{quote(org_name)}/repos"
            f"?per_page={per_page}&page={page}&type=all"
        )
        request = Request(url=url, headers=headers, method="GET")

        try:
            with urlopen(request) as response:
                body = response.read().decode("utf-8")
                current_page = json.loads(body)
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API request failed ({exc.code} {exc.reason}) for org '{org_name}': {error_body}"
            ) from exc

        if not isinstance(current_page, list):
            raise RuntimeError(
                f"Unexpected GitHub API response while listing repositories for org '{org_name}'"
            )

        repos.extend(current_page)

        if len(current_page) < per_page:
            break

        page += 1

    return repos


def write_org_repositories_to_csv(output_csv_path: str, repos: List[Dict[str, Any]]) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=["id", "name", "full_name", "owner/login", "owner/repos_url"],
        )
        writer.writeheader()

        for repo in repos:
            owner_obj = repo.get("owner")
            owner: Dict[str, Any] = owner_obj if isinstance(owner_obj, dict) else {}
            writer.writerow(
                {
                    "id": str(repo.get("id", "")),
                    "name": str(repo.get("name", "")),
                    "full_name": str(repo.get("full_name", "")),
                    "owner/login": str(owner.get("login", "")),
                    "owner/repos_url": str(owner.get("repos_url", "")),
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List all repositories in a GitHub organization and export selected fields to CSV."
    )
    parser.add_argument(
        "--org-name",
        required=True,
        help="GitHub organization name.",
    )
    parser.add_argument(
        "--output-csv",
        required=True,
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--token",
        required=False,
        help="GitHub token. If omitted, GITHUB_TOKEN is used.",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    token = (args.token or os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        parser.error("GitHub token is required via --token or GITHUB_TOKEN")

    try:
        repos = list_org_repositories(token=token, org_name=args.org_name)
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    write_org_repositories_to_csv(output_csv_path=args.output_csv, repos=repos)

    print(f"Total repositories in '{args.org_name}': {len(repos)}")
    print(f"Output CSV: {args.output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
