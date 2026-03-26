import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from get_org_teams import get_team_by_slug, list_org_teams


def list_team_members(token: str, org_name: str, team_slug: str) -> List[Dict[str, Any]]:
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

    members: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while True:
        url = (
            f"https://api.github.com/orgs/{quote(org_name)}/teams/{quote(team_slug)}/members"
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
                f"GitHub API request failed ({exc.code} {exc.reason}) listing members for team '{team_slug}': {error_body}"
            ) from exc

        if not isinstance(current_page, list):
            raise RuntimeError(
                f"Unexpected GitHub API response while listing members for team '{team_slug}'"
            )

        members.extend(current_page)

        if len(current_page) < per_page:
            break

        page += 1

    return members


def write_team_members_to_csv(
    output_csv_path: str,
    rows: List[Dict[str, str]],
) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "team_id",
                "team_name",
                "team_slug",
                "login",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List all teams in a GitHub organization and the members of each team, "
            "including the member's role/permission in the team. Exports results to CSV."
        )
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
        "--team-slug",
        required=False,
        help="Optional team slug. If provided, export members for this team only.",
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

    teams_to_process: List[Dict[str, Any]] = []
    if args.team_slug:
        requested_slug = str(args.team_slug).strip()
        try:
            team = get_team_by_slug(token=token, org_name=args.org_name, team_slug=requested_slug)
        except Exception as exc:
            print(f"CLI failed: {exc}")
            return 1
        teams_to_process = [team]
    else:
        try:
            teams = list_org_teams(token=token, org_name=args.org_name)
        except Exception as exc:
            print(f"CLI failed: {exc}")
            return 1
        teams_to_process = teams

    rows: List[Dict[str, str]] = []
    failed_teams: List[str] = []

    for team in teams_to_process:
        team_id = str(team.get("id", ""))
        team_name = str(team.get("name", ""))
        team_slug = str(team.get("slug", ""))

        try:
            members = list_team_members(token=token, org_name=args.org_name, team_slug=team_slug)
        except Exception as exc:
            print(f"  Failed to list members for team '{team_slug}': {exc}")
            failed_teams.append(team_slug)
            continue

        for member in members:
            rows.append(
                {
                    "team_id": team_id,
                    "team_name": team_name,
                    "team_slug": team_slug,
                    "login": str(member.get("login", "")),
                }
            )

    try:
        write_team_members_to_csv(output_csv_path=args.output_csv, rows=rows)
    except Exception as exc:
        print(f"CLI failed writing CSV: {exc}")
        return 1

    print(
        f"Teams processed: {len(teams_to_process) - len(failed_teams)} succeeded, {len(failed_teams)} failed"
    )
    print(f"Total team-member rows written: {len(rows)}")
    if args.team_slug:
        print(f"Filtered team slug: {args.team_slug}")
    print(f"Output CSV: {args.output_csv}")

    return 0 if not failed_teams else 1


if __name__ == "__main__":
    raise SystemExit(main())
