import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


VALID_PERMISSIONS = {"pull", "triage", "push", "maintain", "admin"}


def assign_team_repo_permission(
    token: str,
    org_name: str,
    team_slug: str,
    repo_name: str,
    permission: str,
) -> Dict[str, Any]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")
    if not team_slug.strip():
        raise ValueError("team_slug is required")
    if not repo_name.strip():
        raise ValueError("repo_name is required")
    if permission not in VALID_PERMISSIONS:
        raise ValueError(
            "permission must be one of: " + ", ".join(sorted(VALID_PERMISSIONS))
        )

    org_escaped = quote(org_name)
    team_escaped = quote(team_slug)
    repo_escaped = quote(repo_name)
    url = f"https://api.github.com/orgs/{org_escaped}/teams/{team_escaped}/repos/{org_escaped}/{repo_escaped}"

    payload = {"permission": permission}
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="PUT",
    )

    try:
        with urlopen(request) as response:
            status_code = getattr(response, "status", response.getcode())
            return {
                "status_code": status_code,
                "org_name": org_name,
                "team_slug": team_slug,
                "repo_name": repo_name,
                "permission": permission,
            }
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API request failed ({exc.code} {exc.reason}) for "
            f"{org_name}/{repo_name} team={team_slug} permission={permission}: {error_body}"
        ) from exc


def assign_team_repos_from_csv(token: str, input_csv_path: str) -> Dict[str, Any]:
    if not token.strip():
        raise ValueError("token is required")
    if not input_csv_path.strip():
        raise ValueError("input_csv_path is required")
    if not os.path.isfile(input_csv_path):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

    successes: List[Dict[str, str]] = []
    failures: List[Dict[str, str]] = []
    api_calls_successful = 0
    api_calls_failed = 0

    with open(input_csv_path, mode="r", newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = set(reader.fieldnames or [])

        required_columns = {"org_name", "team_slug", "repo_name", "permission"}
        missing_columns = sorted(required_columns - fieldnames)
        if missing_columns:
            raise ValueError(
                "Input CSV is missing required columns: " + ", ".join(missing_columns)
            )

        for row_number, row in enumerate(reader, start=2):
            org_name = (row.get("org_name") or "").strip()
            team_slug = (row.get("team_slug") or "").strip()

            if not org_name:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": "",
                        "team_slug": team_slug,
                        "repo_name": "",
                        "reason": "org_name is empty",
                    }
                )
                continue

            if not team_slug:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": "",
                        "repo_name": "",
                        "reason": "team_slug is empty",
                    }
                )
                continue

            repo_name = (row.get("repo_name") or "").strip()
            if not repo_name:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": team_slug,
                        "repo_name": "",
                        "reason": "repo_name is empty",
                    }
                )
                continue

            permission = (row.get("permission") or "").strip().lower()
            if not permission:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": team_slug,
                        "repo_name": repo_name,
                        "reason": "permission is empty",
                    }
                )
                continue

            if permission not in VALID_PERMISSIONS:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": team_slug,
                        "repo_name": repo_name,
                        "reason": (
                            "invalid permission value: "
                            + permission
                            + ". allowed: "
                            + ", ".join(sorted(VALID_PERMISSIONS))
                        ),
                    }
                )
                continue

            try:
                assign_team_repo_permission(
                    token=token,
                    org_name=org_name,
                    team_slug=team_slug,
                    repo_name=repo_name,
                    permission=permission,
                )
                api_calls_successful += 1

                successes.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": team_slug,
                        "repo_name": repo_name,
                        "permissions_applied": permission,
                    }
                )
            except Exception as exc:
                api_calls_failed += 1
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "team_slug": team_slug,
                        "repo_name": repo_name,
                        "reason": str(exc),
                    }
                )

    print("=== Team-repo assignment summary ===")
    print(f"Rows succeeded: {len(successes)}")
    for item in successes:
        print(
            f"[OK] row {item['row']} org='{item['org_name']}' "
            f"team='{item['team_slug']}' repo='{item['repo_name']}' "
            f"permissions={item['permissions_applied']}"
        )

    print(f"Rows failed: {len(failures)}")
    for item in failures:
        print(
            f"[FAILED] row {item['row']} org='{item['org_name']}' "
            f"team='{item['team_slug']}' repo='{item['repo_name']}' "
            f"reason={item['reason']}"
        )

    print(f"API calls successful: {api_calls_successful}")
    print(f"API calls failed: {api_calls_failed}")

    return {
        "success_count": len(successes),
        "failure_count": len(failures),
        "successes": successes,
        "failures": failures,
        "api_calls_successful": api_calls_successful,
        "api_calls_failed": api_calls_failed,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assign GitHub team permissions to repositories from CSV."
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to CSV containing org_name, team_slug, repo_name, permission.",
    )
    parser.add_argument(
        "--token",
        required=False,
        help="GitHub token. Falls back to GITHUB_TOKEN.",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    token = (
        args.token
        or os.getenv("GITHUB_TOKEN")
        or ""
    ).strip()

    if not token:
        parser.error("GitHub token is required via --token or GITHUB_TOKEN")

    try:
        summary = assign_team_repos_from_csv(token=token, input_csv_path=args.input_csv)
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    return 0 if summary["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
