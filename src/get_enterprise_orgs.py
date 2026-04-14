import argparse
import csv
import json
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($enterprise: String!, $cursor: String) {
  enterprise(slug: $enterprise) {
    organizations(first: 100, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        databaseId
        login
        name
        description
        url
      }
    }
  }
}
"""


def _graphql(token: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    request = Request(url=GRAPHQL_URL, data=payload, headers=headers, method="POST")
    try:
        with urlopen(request) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub GraphQL request failed ({exc.code} {exc.reason}): {error_body}"
        ) from exc

    data = json.loads(body)
    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")
    return data


def list_enterprise_organizations(token: str, enterprise: str) -> List[Dict[str, Any]]:
    if not token.strip():
        raise ValueError("token is required")
    if not enterprise.strip():
        raise ValueError("enterprise is required")

    orgs: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        data = _graphql(token, QUERY, {"enterprise": enterprise, "cursor": cursor})

        enterprise_data = data.get("data", {}).get("enterprise")
        if enterprise_data is None:
            raise RuntimeError(
                f"Enterprise '{enterprise}' not found or token lacks 'read:enterprise' scope."
            )

        orgs_page = enterprise_data["organizations"]
        orgs.extend(orgs_page["nodes"])

        page_info = orgs_page["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return orgs


def write_enterprise_organizations_to_csv(output_csv_path: str, orgs: List[Dict[str, Any]]) -> None:
    if not output_csv_path.strip():
        raise ValueError("output_csv_path is required")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=["id", "login", "name", "url", "description"],
        )
        writer.writeheader()

        for org in orgs:
            writer.writerow(
                {
                    "id": str(org.get("databaseId", "")),
                    "login": str(org.get("login", "")),
                    "name": str(org.get("name") or ""),
                    "url": str(org.get("url", "")),
                    "description": str(org.get("description") or ""),
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List all organizations in a GitHub Enterprise account and export selected fields to CSV."
    )
    parser.add_argument(
        "--enterprise",
        required=True,
        help="GitHub Enterprise slug (the short name used in URLs).",
    )
    parser.add_argument(
        "--output-csv",
        required=True,
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--token",
        required=False,
        help="GitHub token. If omitted, GITHUB_TOKEN is used. Requires 'read:enterprise' scope.",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    token = (args.token or os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        parser.error("GitHub token is required via --token or GITHUB_TOKEN")

    try:
        orgs = list_enterprise_organizations(token=token, enterprise=args.enterprise)
    except Exception as exc:
        print(f"CLI failed: {exc}")
        return 1

    write_enterprise_organizations_to_csv(output_csv_path=args.output_csv, orgs=orgs)

    print(f"Total organizations in enterprise '{args.enterprise}': {len(orgs)}")
    print(f"Output CSV: {args.output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
