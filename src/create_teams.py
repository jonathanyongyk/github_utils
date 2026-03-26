import argparse
import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def create_org_team(
	token: str,
	org_name: str,
	team_name: str,
	privacy: str = "closed",
	parent_team_id: Optional[int] = None,
	description: str = "",
) -> Dict[str, Any]:
	"""Create a team in a GitHub organization.

	Args:
		token: GitHub personal access token.
		org_name: Target organization name.
		team_name: Team name to create.
		privacy: Team privacy (closed or secret).
		parent_team_id: Optional parent team id for nested team creation.
		description: Optional team description.

	Returns:
		Parsed JSON response from GitHub.

	Raises:
		RuntimeError: If the API call fails.
	"""
	if not token.strip():
		raise ValueError("token is required")
	if not org_name.strip():
		raise ValueError("org_name is required")
	if not team_name.strip():
		raise ValueError("team_name is required")
	if privacy not in {"closed", "secret"}:
		raise ValueError("privacy must be 'closed' or 'secret'")

	url = f"https://api.github.com/orgs/{quote(org_name)}/teams"
	payload: Dict[str, Any] = {
		"name": team_name,
		"privacy": privacy,
		"description": description,
	}
	if parent_team_id is not None:
		payload["parent_team_id"] = parent_team_id

	req = Request(
		url=url,
		data=json.dumps(payload).encode("utf-8"),
		headers={
			"Accept": "application/vnd.github+json",
			"Authorization": f"Bearer {token}",
			"X-GitHub-Api-Version": "2022-11-28",
			"Content-Type": "application/json",
		},
		method="POST",
	)

	try:
		with urlopen(req) as response:
			body = response.read().decode("utf-8")
			return json.loads(body)
	except HTTPError as exc:
		error_body = exc.read().decode("utf-8", errors="replace")
		raise RuntimeError(
			f"GitHub API request failed ({exc.code} {exc.reason}): {error_body}"
		) from exc


def _resolve_org_team_and_privacy(row: Dict[str, str]) -> Tuple[str, str, str, str]:
	org_value = (row.get("org_name") or "").strip()
	team_value = (row.get("team_name") or "").strip()
	privacy_value = (row.get("privacy") or "").strip().lower()
	parent_team_value = (row.get("parent_team") or "").strip()
	return org_value, team_value, privacy_value, parent_team_value


def _to_team_slug(team_name: str) -> str:
	return "-".join(team_name.strip().lower().split())


def _lookup_parent_team_id_on_demand(
	token: str,
	org_name: str,
	parent_team_name: str,
	org_parent_cache: Dict[str, Dict[str, int]],
) -> int:
	headers = {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {token}",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	org_key = org_name.lower()
	cache_for_org = org_parent_cache.setdefault(org_key, {})
	parent_lookup_key = parent_team_name.lower()
	team_slug = _to_team_slug(parent_team_name)
	url = f"https://api.github.com/orgs/{quote(org_name)}/teams/{quote(team_slug)}"
	req = Request(url=url, headers=headers, method="GET")
	try:
		with urlopen(req) as response:
			body = response.read().decode("utf-8")
			team = json.loads(body)
	except HTTPError as exc:
		error_body = exc.read().decode("utf-8", errors="replace")
		if exc.code == 404:
			raise ValueError(
				f"parent_team '{parent_team_name}' not found in org '{org_name}'"
			) from exc
		raise RuntimeError(
			f"Failed to lookup parent_team '{parent_team_name}' in org '{org_name}' "
			f"({exc.code} {exc.reason}): {error_body}"
		) from exc

	if not isinstance(team, dict):
		raise RuntimeError(
			f"Unexpected response when looking up parent_team '{parent_team_name}' in org '{org_name}'"
		)

	team_id_raw = team.get("id")
	if not isinstance(team_id_raw, int):
		raise RuntimeError(
			f"Parent team lookup for '{parent_team_name}' in org '{org_name}' returned invalid id"
		)

	resolved_team_name = str(team.get("name", "")).strip()
	cache_for_org[parent_lookup_key] = team_id_raw
	if resolved_team_name:
		cache_for_org[resolved_team_name.lower()] = team_id_raw

	return team_id_raw


def _get_parent_team_id(
	token: str,
	org_name: str,
	parent_team_name: str,
	org_parent_cache: Dict[str, Dict[str, int]],
) -> int:
	org_key = org_name.lower()
	cache_for_org = org_parent_cache.setdefault(org_key, {})
	parent_lookup_key = parent_team_name.lower()
	parent_id = cache_for_org.get(parent_lookup_key)
	if parent_id is not None:
		return parent_id

	return _lookup_parent_team_id_on_demand(
		token=token,
		org_name=org_name,
		parent_team_name=parent_team_name,
		org_parent_cache=org_parent_cache,
	)


def _write_success_csv(output_csv_path: str, successes: List[Dict[str, str]]) -> None:
	with open(output_csv_path, mode="w", newline="", encoding="utf-8") as outfile:
		writer = csv.DictWriter(
			outfile,
			fieldnames=["team_id", "org_name", "team_name", "team_slug"],
		)
		writer.writeheader()
		for item in successes:
			writer.writerow(
				{
					"team_id": item["team_id"],
					"org_name": item["organization"],
					"team_name": item["team_name"],
					"team_slug": item["team_slug"],
				}
			)


def create_teams_from_csv(
	token: str,
	input_csv_path: str,
	output_csv_path: Optional[str] = None,
) -> Dict[str, Any]:
	"""Create organization teams from a CSV file.

	Required CSV columns:
		- org_name
		- team_name
		- privacy
		- parent_team

	Args:
		token: GitHub personal access token.
		input_csv_path: Path to input CSV.
		output_csv_path: Optional output CSV path for successful team rows.

	Returns:
		Summary dictionary with successes and failures.
	"""
	if not token.strip():
		raise ValueError("token is required")
	if not input_csv_path.strip():
		raise ValueError("input_csv_path is required")
	if not os.path.isfile(input_csv_path):
		raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

	successes: List[Dict[str, str]] = []
	failures: List[Dict[str, str]] = []
	org_parent_cache: Dict[str, Dict[str, int]] = {}

	with open(input_csv_path, mode="r", newline="", encoding="utf-8-sig") as infile:
		reader = csv.DictReader(infile)
		fieldnames = set(reader.fieldnames or [])
		required_columns = {"org_name", "team_name", "privacy", "parent_team"}
		missing_columns = sorted(required_columns - fieldnames)
		if missing_columns:
			raise ValueError(
				"Input CSV is missing required columns: " + ", ".join(missing_columns)
			)

		for row_number, row in enumerate(reader, start=2):
			org_name, team_name, row_privacy, parent_team = _resolve_org_team_and_privacy(row)

			if not org_name:
				failures.append(
					{
						"row": str(row_number),
						"organization": "",
						"team_name": team_name,
						"reason": "organization is empty",
					}
				)
				continue

			if not team_name:
				failures.append(
					{
						"row": str(row_number),
						"organization": org_name,
						"team_name": "",
						"reason": "team_name is empty",
					}
				)
				continue

			if not row_privacy:
				failures.append(
					{
						"row": str(row_number),
						"organization": org_name,
						"team_name": team_name,
						"reason": "privacy is empty",
					}
				)
				continue

			if row_privacy not in {"closed", "secret"}:
				failures.append(
					{
						"row": str(row_number),
						"organization": org_name,
						"team_name": team_name,
						"reason": "privacy must be 'closed' or 'secret'",
					}
				)
				continue

			parent_team_id: Optional[int] = None
			if parent_team:
				try:
					parent_team_id = _get_parent_team_id(
						token=token,
						org_name=org_name,
						parent_team_name=parent_team,
						org_parent_cache=org_parent_cache,
					)
				except Exception as exc:
					failures.append(
						{
							"row": str(row_number),
							"organization": org_name,
							"team_name": team_name,
							"reason": str(exc),
						}
					)
					continue

			try:
				response = create_org_team(
					token=token,
					org_name=org_name,
					team_name=team_name,
					privacy=row_privacy,
					parent_team_id=parent_team_id,
				)
				created_team_name = str(response.get("name", team_name)).strip()
				created_team_id = response.get("id")
				if created_team_name and isinstance(created_team_id, int):
					org_key = org_name.lower()
					if org_key not in org_parent_cache:
						org_parent_cache[org_key] = {}
					org_parent_cache[org_key][created_team_name.lower()] = created_team_id
				successes.append(
					{
						"organization": org_name,
						"team_name": created_team_name or team_name,
						"team_slug": response.get("slug", ""),
						"team_id": str(response.get("id", "")),
					}
				)
			except Exception as exc:
				failures.append(
					{
						"row": str(row_number),
						"organization": org_name,
						"team_name": team_name,
						"reason": str(exc),
					}
				)

	print("=== Team creation summary ===")
	print(f"Successful: {len(successes)}")
	for item in successes:
		print(
			f"[OK] {item['organization']} / {item['team_name']}"
			f" (slug: {item['team_slug']}, id: {item['team_id']})"
		)

	print(f"Failed: {len(failures)}")
	for item in failures:
		print(
			f"[FAILED] row {item['row']} org '{item['organization']}' "
			f"team '{item['team_name']}' - {item['reason']}"
		)

	if output_csv_path:
		_write_success_csv(output_csv_path=output_csv_path, successes=successes)
		print(f"Success count: {len(successes)}")
		print(f"Output CSV: {output_csv_path}")

	return {
		"success_count": len(successes),
		"failure_count": len(failures),
		"successes": successes,
		"failures": failures,
	}


def _build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Create GitHub organization teams from CSV"
	)
	parser.add_argument(
		"--input-csv",
		required=True,
		help="Path to input CSV containing org_name, team_name, privacy, parent_team columns",
	)
	parser.add_argument(
		"--token",
		required=False,
		help="GitHub token. If omitted, GITHUB_TOKEN is used.",
	)
	parser.add_argument(
		"--output-csv",
		required=True,
		help="Output CSV file path for successful rows (team_id, org_name, team_name, team_slug)",
	)
	return parser


def main() -> int:
	parser = _build_arg_parser()
	args = parser.parse_args()

	token = (
		(args.token or os.getenv("GITHUB_TOKEN") or "")
		.strip()
	)
	if not token:
		parser.error("GitHub token is required via --token or GITHUB_TOKEN")

	if not os.path.isfile(args.input_csv):
		print(f"Input CSV file not found: {args.input_csv}")
		return 1

	try:
		create_teams_from_csv(
			token=token,
			input_csv_path=args.input_csv,
			output_csv_path=args.output_csv,
		)
		return 0
	except Exception as exc:
		print(f"CLI failed: {exc}")
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
