import json
import csv
import os
import argparse
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def create_github_repo(
	token: str,
	repo_name: str,
	org: Optional[str] = None,
	description: str = "",
) -> Dict[str, Any]:
	"""Create a private, empty GitHub repository using the REST API.

	Args:
		token: GitHub personal access token with `repo` scope.
		repo_name: New repository name.
		org: Organization name. If omitted, creates under the authenticated user.
		description: Optional repository description.

	Returns:
		Parsed JSON response from GitHub.

	Raises:
		RuntimeError: If the API call fails.
	"""
	if not token.strip():
		raise ValueError("token is required")
	if not repo_name.strip():
		raise ValueError("repo_name is required")

	if org:
		url = f"https://api.github.com/orgs/{quote(org)}/repos"
	else:
		url = "https://api.github.com/user/repos"

	payload = {
		"name": repo_name,
		"description": description,
		"private": True,
		# Keep repository empty: do not create README/.gitignore/license.
		"auto_init": False,
	}

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


def add_repo_admin(
	token: str,
	owner: str,
	repo_name: str,
	username: str,
) -> Dict[str, Any]:
	"""Assign a user as an admin collaborator on a GitHub repository.

	Args:
		token: GitHub personal access token with admin access to the repo.
		owner: Repository owner (user or organization).
		repo_name: Repository name.
		username: GitHub username to add as collaborator.

	Returns:
		A dictionary with request status and any API response payload.

	Raises:
		RuntimeError: If the API call fails.
	"""
	if not token.strip():
		raise ValueError("token is required")
	if not owner.strip():
		raise ValueError("owner is required")
	if not repo_name.strip():
		raise ValueError("repo_name is required")
	if not username.strip():
		raise ValueError("username is required")

	url = (
		f"https://api.github.com/repos/{quote(owner)}/{quote(repo_name)}"
		f"/collaborators/{quote(username)}"
	)
	payload = {"permission": "admin"}

	req = Request(
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
		with urlopen(req) as response:
			body = response.read().decode("utf-8")
			parsed_body = json.loads(body) if body else None
			return {
				"status": response.status,
				"body": parsed_body,
			}
	except HTTPError as exc:
		error_body = exc.read().decode("utf-8", errors="replace")
		raise RuntimeError(
			f"GitHub API request failed ({exc.code} {exc.reason}): {error_body}"
		) from exc


def create_repo_and_assign_admin(
	token: str,
	repo_name: str,
	admin_username: str,
	owner: Optional[str] = None,
	description: str = "",
) -> Dict[str, Any]:
	"""Create a private empty repo and assign an admin collaborator.

	The admin assignment is executed only if repository creation succeeds.

	Args:
		token: GitHub personal access token.
		repo_name: New repository name.
		admin_username: GitHub username to grant admin access.
		owner: Organization/user owner. If provided, repo is created in that org.
		description: Optional repository description.

	Returns:
		A dictionary with the create-repo and add-admin API results.

	Raises:
		RuntimeError: If either API call fails.
	"""
	repo_response = create_github_repo(
		token=token,
		repo_name=repo_name,
		org=owner,
		description=description,
	)

	resolved_owner = owner or repo_response.get("owner", {}).get("login")
	if not resolved_owner:
		raise RuntimeError(
			"Repository was created, but owner could not be determined for admin assignment."
		)

	admin_response = add_repo_admin(
		token=token,
		owner=resolved_owner,
		repo_name=repo_name,
		username=admin_username,
	)

	return {
		"repository": repo_response,
		"admin_assignment": admin_response,
	}


def create_repos_from_csv(
	token: str,
	input_csv_path: str,
	output_success_csv_path: str,
) -> Dict[str, Any]:
	"""Create repositories from CSV rows and export successful results.

	Required input columns:
		organization, repo_name, repo_description, repo_admin

	Args:
		token: GitHub personal access token.
		input_csv_path: Path to source CSV with repository rows.
		output_success_csv_path: Path to write successful repo name/url rows.

	Returns:
		A summary dictionary with success and failure details.
	"""
	if not token.strip():
		raise ValueError("token is required")
	if not input_csv_path.strip():
		raise ValueError("input_csv_path is required")
	if not output_success_csv_path.strip():
		raise ValueError("output_success_csv_path is required")
	if not os.path.isfile(input_csv_path):
		raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

	required_columns = {
		"organization",
		"repo_name",
		"repo_description",
		"repo_admin",
	}
	successes: List[Dict[str, str]] = []
	failures: List[Dict[str, str]] = []

	with open(input_csv_path, mode="r", newline="", encoding="utf-8-sig") as infile:
		reader = csv.DictReader(infile)
		fieldnames = set(reader.fieldnames or [])
		missing = sorted(required_columns - fieldnames)
		if missing:
			raise ValueError(
				"Input CSV is missing required columns: " + ", ".join(missing)
			)

		for row_number, row in enumerate(reader, start=2):
			organization = (row.get("organization") or "").strip()
			repo_name = (row.get("repo_name") or "").strip()
			repo_description = (row.get("repo_description") or "").strip()
			repo_admin = (row.get("repo_admin") or "").strip()

			if not repo_name:
				failures.append(
					{
						"row": str(row_number),
						"repo_name": "",
						"reason": "repo_name is empty",
					}
				)
				continue

			if not repo_admin:
				failures.append(
					{
						"row": str(row_number),
						"repo_name": repo_name,
						"reason": "repo_admin is empty",
					}
				)
				continue

			try:
				result = create_repo_and_assign_admin(
					token=token,
					repo_name=repo_name,
					admin_username=repo_admin,
					owner=organization or None,
					description=repo_description,
				)
				repo_info = result.get("repository", {})
				successes.append(
					{
						"repo_name": repo_info.get("name", repo_name),
						"repo_url": repo_info.get("html_url", ""),
					}
				)
			except Exception as exc:
				failures.append(
					{
						"row": str(row_number),
						"repo_name": repo_name,
						"reason": str(exc),
					}
				)

	with open(
		output_success_csv_path,
		mode="w",
		newline="",
		encoding="utf-8",
	) as outfile:
		writer = csv.DictWriter(outfile, fieldnames=["repo_name", "repo_url"])
		writer.writeheader()
		writer.writerows(successes)

	print("=== Repository creation summary ===")
	print(f"Successful: {len(successes)}")
	for item in successes:
		print(f"[OK] {item['repo_name']} - {item['repo_url']}")

	print(f"Failed: {len(failures)}")
	for item in failures:
		print(
			f"[FAILED] row {item['row']} repo '{item['repo_name']}' - {item['reason']}"
		)

	return {
		"success_count": len(successes),
		"failure_count": len(failures),
		"successes": successes,
		"failures": failures,
		"output_success_csv_path": output_success_csv_path,
	}


def _build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description=(
			"Create private empty GitHub repositories from CSV and assign repo admins."
		)
	)
	parser.add_argument(
		"--input-csv",
		required=True,
		help="Path to input CSV with columns: organization, repo_name, repo_description, repo_admin",
	)
	parser.add_argument(
		"--output-csv",
		required=True,
		help="Path to output CSV file for successfully created repositories",
	)
	parser.add_argument(
		"--token",
		required=False,
		help="GitHub token. If omitted, GITHUB_TOKEN environment variable is used.",
	)
	return parser


def main() -> int:
	parser = _build_arg_parser()
	args = parser.parse_args()

	token = (args.token or os.getenv("GITHUB_TOKEN") or "").strip()
	if not token:
		parser.error("GitHub token is required via --token or GITHUB_TOKEN")

	if not os.path.isfile(args.input_csv):
		print(f"Input CSV file not found: {args.input_csv}")
		return 1

	try:
		create_repos_from_csv(
			token=token,
			input_csv_path=args.input_csv,
			output_success_csv_path=args.output_csv,
		)
		return 0
	except Exception as exc:
		print(f"CLI failed: {exc}")
		return 1


if __name__ == "__main__":
	raise SystemExit(main())

