import argparse
import csv
import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


VALID_ORG_ROLES = {"member", "admin"}


def assign_user_to_organization(
    token: str,
    org_name: str,
    username: str,
    role_name: str,
) -> Dict[str, Any]:
    if not token.strip():
        raise ValueError("token is required")
    if not org_name.strip():
        raise ValueError("org_name is required")
    if not username.strip():
        raise ValueError("username is required")
    if role_name not in VALID_ORG_ROLES:
        raise ValueError("role_name must be one of: " + ", ".join(sorted(VALID_ORG_ROLES)))

    url = f"https://api.github.com/orgs/{quote(org_name)}/memberships/{quote(username)}"
    payload = {"role": role_name}

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
            body = response.read().decode("utf-8")
            parsed_body = json.loads(body) if body else {}
            return {
                "status_code": getattr(response, "status", response.getcode()),
                "org_name": org_name,
                "username": username,
                "state": str(parsed_body.get("state", "")),
                "role": str(parsed_body.get("role", role_name)),
            }
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API request failed ({exc.code} {exc.reason}) for "
            f"org={org_name} username={username}: {error_body}"
        ) from exc


def assign_users_from_csv(token: str, input_csv_path: str) -> Dict[str, Any]:
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
        required_columns = {"org_name", "username", "role_name"}
        missing_columns = sorted(required_columns - fieldnames)
        if missing_columns:
            raise ValueError(
                "Input CSV is missing required columns: " + ", ".join(missing_columns)
            )

        for row_number, row in enumerate(reader, start=2):
            org_name = (row.get("org_name") or "").strip()
            username = (row.get("username") or "").strip()
            role_name = (row.get("role_name") or "").strip().lower()

            if not org_name:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": "",
                        "username": username,
                        "reason": "org_name is empty",
                    }
                )
                continue

            if not username:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "username": "",
                        "reason": "username is empty",
                    }
                )
                continue

            if not role_name:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "username": username,
                        "reason": "role_name is empty",
                    }
                )
                continue

            if role_name not in VALID_ORG_ROLES:
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "username": username,
                        "reason": "invalid role_name value: "
                        + role_name
                        + ". allowed: "
                        + ", ".join(sorted(VALID_ORG_ROLES)),
                    }
                )
                continue

            try:
                result = assign_user_to_organization(
                    token=token,
                    org_name=org_name,
                    username=username,
                    role_name=role_name,
                )
                api_calls_successful += 1
                successes.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "username": username,
                        "role_name": role_name,
                        "state": str(result.get("state", "")),
                        "role": str(result.get("role", role_name)),
                    }
                )
            except Exception as exc:
                api_calls_failed += 1
                failures.append(
                    {
                        "row": str(row_number),
                        "org_name": org_name,
                        "username": username,
                        "reason": str(exc),
                    }
                )

    print("=== Organization user assignment summary ===")
    print(f"Rows succeeded: {len(successes)}")
    for item in successes:
        print(
            f"[OK] row {item['row']} org='{item['org_name']}' "
            f"username='{item['username']}' role_name={item['role_name']} "
            f"state={item['state']} role={item['role']}"
        )

    print(f"Rows failed: {len(failures)}")
    for item in failures:
        print(
            f"[FAILED] row {item['row']} org='{item['org_name']}' "
            f"username='{item['username']}' reason={item['reason']}"
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
        description="Assign EMU users to GitHub organizations from CSV."
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to CSV containing org_name, username, role_name.",
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

    token = (args.token or os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        parser.error("GitHub token is required via --token or GITHUB_TOKEN")

    try:
        summary = assign_users_from_csv(token=token, input_csv_path=args.input_csv)
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    return 0 if summary["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
