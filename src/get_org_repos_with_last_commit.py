import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def _parse_last_link(link_header: str) -> str:
    """Return the URL for rel="last" from a GitHub Link header, or empty string."""
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="last"' in part:
            url_part = part.split(";")[0].strip()
            return url_part.strip("<>")
    return ""


def get_repo_commit_info(full_name: str, headers: Dict[str, str]) -> tuple:
    """Return (creator_login, last_commit_author_login) for the given repo."""
    url = f"https://api.github.com/repos/{full_name}/commits?per_page=1"
    request = Request(url=url, headers=headers, method="GET")
    try:
        with urlopen(request) as response:
            link_header = response.getheader("Link", "")
            body = response.read().decode("utf-8")
            latest_commits = json.loads(body)

        last_commit_author = ""
        if latest_commits:
            author = latest_commits[0].get("author") or {}
            last_commit_author = str(author.get("login", ""))

        creator = ""
        last_url = _parse_last_link(link_header)
        if last_url:
            request2 = Request(url=last_url, headers=headers, method="GET")
            with urlopen(request2) as response2:
                oldest_commits = json.loads(response2.read().decode("utf-8"))
            if oldest_commits:
                author = oldest_commits[-1].get("author") or {}
                creator = str(author.get("login", ""))
        elif latest_commits:
            # Only one page: the oldest commit is the last item on the first page
            author = latest_commits[-1].get("author") or {}
            creator = str(author.get("login", ""))

        return creator, last_commit_author
    except Exception:
        return "", ""


def list_org_repositories(token: str, org_name: str) -> tuple:
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

    return repos, headers


def write_org_repositories_to_csv(output_csv_path: str, repos: List[Dict[str, Any]], headers: Dict[str, str]) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=["id", "name", "full_name", "owner/login", "owner/repos_url", "creator", "last_commit_author", "last_commit_date"],
        )
        writer.writeheader()

        for repo in repos:
            owner_obj = repo.get("owner")
            owner: Dict[str, Any] = owner_obj if isinstance(owner_obj, dict) else {}
            full_name = str(repo.get("full_name", ""))
            creator, last_commit_author = get_repo_commit_info(full_name, headers) if full_name else ("", "")
            writer.writerow(
                {
                    "id": str(repo.get("id", "")),
                    "name": str(repo.get("name", "")),
                    "full_name": full_name,
                    "owner/login": str(owner.get("login", "")),
                    "owner/repos_url": str(owner.get("repos_url", "")),
                    "last_commit_date": str(repo.get("pushed_at", "")),
                    "last_commit_author": last_commit_author,
                    "creator": creator,
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List all repositories in a GitHub organization and export selected fields to CSV, including last commit date."
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
        repos, headers = list_org_repositories(token=token, org_name=args.org_name)
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    write_org_repositories_to_csv(output_csv_path=args.output_csv, repos=repos, headers=headers)

    print(f"Total repositories in '{args.org_name}': {len(repos)}")
    print(f"Output CSV: {args.output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
