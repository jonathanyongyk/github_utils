import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def list_org_teams(token: str, org_name: str) -> List[Dict[str, Any]]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    teams: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while True:
        url = (
            f"https://api.github.com/orgs/{quote(org_name)}/teams"
            f"?per_page={per_page}&page={page}"
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
                f"Unexpected GitHub API response while listing teams for org '{org_name}'"
            )

        teams.extend(current_page)

        if len(current_page) < per_page:
            break

        page += 1

    return teams


def write_org_teams_to_csv(output_csv_path: str, org_name: str, teams: List[Dict[str, Any]]) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")
    if not org_name.strip():
        raise ValueError("org_name is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "id",
                "org_name",
                "team_name",
                "team_slug",
                "privacy",
                "parent",
                "parent_team_slug",
            ],
        )
        writer.writeheader()

        for team in teams:
            parent_obj = team.get("parent")
            parent_team = parent_obj if isinstance(parent_obj, dict) else {}
            writer.writerow(
                {
                    "id": str(team.get("id", "")),
                    "org_name": org_name,
                    "team_name": str(team.get("name", "")),
                    "team_slug": str(team.get("slug", "")),
                    "privacy": str(team.get("privacy", "")),
                    "parent": str(parent_team.get("name", "")),
                    "parent_team_slug": str(parent_team.get("slug", "")),
                }
            )


def get_team_by_slug(token: str, org_name: str, team_slug: str) -> Dict[str, Any]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")
    if not team_slug.strip():
        raise ValueError("team_slug is required")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/orgs/{quote(org_name)}/teams/{quote(team_slug)}"
    request = Request(url=url, headers=headers, method="GET")

    try:
        with urlopen(request) as response:
            body = response.read().decode("utf-8")
            team = json.loads(body)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API request failed ({exc.code} {exc.reason}) fetching team '{team_slug}': {error_body}"
        ) from exc

    if not isinstance(team, dict):
        raise RuntimeError(
            f"Unexpected GitHub API response while fetching team '{team_slug}'"
        )

    return team


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List all teams in a GitHub organization and export selected fields to CSV."
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
        teams = list_org_teams(token=token, org_name=args.org_name)
        write_org_teams_to_csv(
            output_csv_path=args.output_csv,
            org_name=args.org_name,
            teams=teams,
        )
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    print(f"Total teams in '{args.org_name}': {len(teams)}")
    print(f"Output CSV: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
