import argparse
import csv
import json
import os
from typing import Any, Dict, List, Set
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def list_org_members(token: str, org_name: str, role: str = "all") -> List[Dict[str, Any]]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")
    if role not in {"all", "admin", "member"}:
        raise ValueError("role must be one of: all, admin, member")

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
            f"https://api.github.com/orgs/{quote(org_name)}/members"
            f"?per_page={per_page}&page={page}&role={role}"
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
                f"Unexpected GitHub API response while listing members for org '{org_name}'"
            )

        for item in current_page:
            if isinstance(item, dict):
                members.append(item)

        if len(current_page) < per_page:
            break

        page += 1

    return members


def write_members_to_csv(
    output_csv_path: str,
    members: List[Dict[str, Any]],
    admin_logins: Set[str],
) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["id", "username", "role_name"])
        writer.writeheader()
        for member in members:
            username = str(member.get("login", ""))
            role_name = "admin" if username in admin_logins else "member"
            writer.writerow(
                {
                    "id": str(member.get("id", "")),
                    "username": username,
                    "role_name": role_name,
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export organization members (id, username, role_name) to CSV."
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
        members = list_org_members(token=token, org_name=args.org_name, role="all")
        admin_members = list_org_members(token=token, org_name=args.org_name, role="admin")
        admin_logins = {
            str(member.get("login", ""))
            for member in admin_members
            if str(member.get("login", ""))
        }
        write_members_to_csv(
            output_csv_path=args.output_csv,
            members=members,
            admin_logins=admin_logins,
        )
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    print(f"Total members in '{args.org_name}': {len(members)}")
    print(f"Output CSV: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
