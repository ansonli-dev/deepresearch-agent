#!/usr/bin/env python3
"""
Sync DeepResearch Agent issues to Linear via GraphQL API.

Usage:
  1. Get your Linear API key from: Settings > Security & Access > API
  2. Find your Team ID by running: python sync_to_linear.py --discover
  3. Run sync: python sync_to_linear.py --api-key <KEY> --team-id <ID>

Options:
  --dry-run         Preview what would be created without making API calls
  --milestone P0    Only sync a specific milestone (P0, M1, M2, M3, M4, M5)
  --issues-file     Path to issues JSON file (default: linear_issues.json)
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency. Install with: pip install requests")
    sys.exit(1)


LINEAR_API_URL = "https://api.linear.app/graphql"

# Priority mapping: Linear uses 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
PRIORITY_MAP = {1: 1, 2: 2, 3: 3, 4: 4}


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": api_key,
        }
        self._label_cache: dict[str, str] = {}
        self._cycle_cache: dict[str, str] = {}

    def _request(self, query: str, variables: dict | None = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(LINEAR_API_URL, json=payload, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        return data["data"]

    # ── Discovery ──

    def get_teams(self) -> list[dict]:
        data = self._request("{ teams { nodes { id name key } } }")
        return data["teams"]["nodes"]

    def get_labels(self, team_id: str) -> list[dict]:
        data = self._request(
            """query { issueLabels(first: 100) { nodes { id name color } } }"""
        )
        return data["issueLabels"]["nodes"]

    def get_workspace_labels(self) -> list[dict]:
        # Already covered by get_labels (returns all labels without filter)
        return []

    def get_cycles(self, team_id: str) -> list[dict]:
        data = self._request(
            """{ teams { nodes { id cycles { nodes { id name number } } } } }"""
        )
        for t in data["teams"]["nodes"]:
            if t["id"] == team_id:
                return t["cycles"]["nodes"]
        return []

    def get_workflow_states(self, team_id: str) -> list[dict]:
        data = self._request(
            """{ teams { nodes { id states { nodes { id name type } } } } }"""
        )
        for t in data["teams"]["nodes"]:
            if t["id"] == team_id:
                return t["states"]["nodes"]
        return []

    # ── Create ──

    def create_label(self, team_id: str, name: str, color: str) -> str:
        data = self._request(
            """mutation($input: IssueLabelCreateInput!) {
                issueLabelCreate(input: $input) {
                    success
                    issueLabel { id name }
                }
            }""",
            {"input": {"teamId": team_id, "name": name, "color": color}},
        )
        label = data["issueLabelCreate"]["issueLabel"]
        print(f"  ✓ Created label: {label['name']}")
        return label["id"]

    def create_cycle(self, team_id: str, name: str, start: str, end: str) -> str:
        data = self._request(
            """mutation($input: CycleCreateInput!) {
                cycleCreate(input: $input) {
                    success
                    cycle { id name number }
                }
            }""",
            {"input": {"teamId": team_id, "name": name, "startsAt": start, "endsAt": end}},
        )
        cycle = data["cycleCreate"]["cycle"]
        print(f"  ✓ Created cycle: {cycle['name']} (#{cycle['number']})")
        return cycle["id"]

    def create_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        priority: int = 0,
        estimate: int | None = None,
        label_ids: list[str] | None = None,
        cycle_id: str | None = None,
    ) -> dict:
        input_data: dict = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if estimate is not None:
            input_data["estimate"] = estimate
        if label_ids:
            input_data["labelIds"] = label_ids
        if cycle_id:
            input_data["cycleId"] = cycle_id

        data = self._request(
            """mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue { id identifier title }
                }
            }""",
            {"input": input_data},
        )
        return data["issueCreate"]["issue"]

    # ── Helpers ──

    def ensure_labels(self, team_id: str, label_defs: list[dict]) -> dict[str, str]:
        """Create labels if they don't exist. Returns name→id mapping."""
        existing = self.get_labels(team_id) + self.get_workspace_labels()
        name_to_id = {l["name"].lower(): l["id"] for l in existing}

        for ldef in label_defs:
            key = ldef["name"].lower()
            if key not in name_to_id:
                lid = self.create_label(team_id, ldef["name"], ldef["color"])
                name_to_id[key] = lid
            else:
                print(f"  · Label exists: {ldef['name']}")

        self._label_cache = name_to_id
        return name_to_id

    def resolve_label_ids(self, label_names: list[str]) -> list[str]:
        return [
            self._label_cache[n.lower()]
            for n in label_names
            if n.lower() in self._label_cache
        ]


def _fetch_existing_titles(client: LinearClient, team_id: str) -> set[str]:
    """Fetch all existing issue titles in the team for deduplication."""
    query = """query($after: String) {
        issues(first: 100, after: $after) {
            nodes { title }
            pageInfo { hasNextPage endCursor }
        }
    }"""
    titles: set[str] = set()
    cursor = None
    while True:
        variables: dict = {}
        if cursor:
            variables["after"] = cursor
        data = client._request(query, variables if variables else None)
        for node in data["issues"]["nodes"]:
            titles.add(node["title"])
        page_info = data["issues"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return titles


def discover(api_key: str):
    """Print team info to help user find their team ID."""
    client = LinearClient(api_key)

    print("\n📋 Your Linear Teams:")
    print("-" * 60)
    teams = client.get_teams()
    for t in teams:
        print(f"  Team: {t['name']}  Key: {t['key']}  ID: {t['id']}")

    if teams:
        team_id = teams[0]["id"]
        print(f"\n🏷️  Labels in '{teams[0]['name']}':")
        for l in client.get_labels(team_id):
            print(f"  {l['name']} ({l['color']})")

        print(f"\n🔄 Cycles in '{teams[0]['name']}':")
        for c in client.get_cycles(team_id):
            print(f"  #{c['number']}: {c.get('name', '(unnamed)')}")

        print(f"\n📊 Workflow States in '{teams[0]['name']}':")
        for s in client.get_workflow_states(team_id):
            print(f"  {s['name']} ({s['type']})")

    print("\n" + "=" * 60)
    print("Use --team-id <ID> with the team ID above to sync issues.")


def sync(
    api_key: str,
    team_id: str,
    issues_file: str,
    dry_run: bool = False,
    milestone_filter: str | None = None,
):
    """Sync issues from JSON to Linear."""
    path = Path(issues_file)
    if not path.exists():
        print(f"❌ Issues file not found: {issues_file}")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    client = LinearClient(api_key)

    # 1. Ensure labels exist
    print("\n🏷️  Ensuring labels...")
    if dry_run:
        print("  [DRY RUN] Would create labels:", [l["name"] for l in data["labels"]])
        label_map = {l["name"].lower(): f"fake-{l['name']}" for l in data["labels"]}
        client._label_cache = label_map
    else:
        label_map = client.ensure_labels(team_id, data["labels"])

    # 2. Filter milestones
    milestones = data["milestones"]
    if milestone_filter:
        milestones = [m for m in milestones if m["id"] == milestone_filter]
        if not milestones:
            print(f"❌ Milestone '{milestone_filter}' not found.")
            print(f"   Available: {', '.join(m['id'] for m in data['milestones'])}")
            sys.exit(1)

    # 3. Fetch existing issues for dedup
    existing_titles: set[str] = set()
    if not dry_run:
        print("\n🔍 Fetching existing issues for dedup...")
        existing_titles = _fetch_existing_titles(client, team_id)
        print(f"  Found {len(existing_titles)} existing issues")

    # 4. Create issues per milestone
    total_created = 0
    total_skipped = 0
    for ms in milestones:
        print(f"\n{'='*60}")
        print(f"📌 {ms['title']} ({ms['duration']})")
        print(f"   {ms['description']}")
        print(f"   Issues: {len(ms['issues'])}")
        print(f"{'='*60}")

        # Note: Cycles require start/end dates. We skip auto-creation here
        # and let the user create cycles manually in Linear, or pass cycle IDs.
        cycle_id = None

        for i, issue in enumerate(ms["issues"], 1):
            label_ids = client.resolve_label_ids(issue["labels"])
            priority = PRIORITY_MAP.get(issue["priority"], 0)

            if dry_run:
                print(f"\n  [{i}/{len(ms['issues'])}] [DRY RUN] Would create:")
                print(f"    Title:    {issue['title']}")
                print(f"    Labels:   {issue['labels']}")
                print(f"    Priority: {priority}")
                print(f"    Estimate: {issue['estimate']} pts")
                print(f"    Desc:     {len(issue['description'])} chars")
            else:
                if issue["title"] in existing_titles:
                    print(f"  · [{i}/{len(ms['issues'])}] SKIP (exists): {issue['title']}")
                    total_skipped += 1
                    continue

                try:
                    result = client.create_issue(
                        team_id=team_id,
                        title=issue["title"],
                        description=issue["description"],
                        priority=priority,
                        estimate=issue["estimate"],
                        label_ids=label_ids,
                        cycle_id=cycle_id,
                    )
                    print(f"  ✓ [{i}/{len(ms['issues'])}] {result['identifier']}: {result['title']}")
                    total_created += 1
                    existing_titles.add(issue["title"])

                    # Rate limiting: Linear API allows ~100 req/min
                    time.sleep(0.6)

                except Exception as e:
                    print(f"  ✗ [{i}/{len(ms['issues'])}] FAILED: {issue['title']}")
                    print(f"    Error: {e}")

    print(f"\n{'='*60}")
    if dry_run:
        total = sum(len(ms["issues"]) for ms in milestones)
        print(f"🏁 DRY RUN complete. Would create {total} issues.")
    else:
        print(f"🏁 Sync complete. Created {total_created} issues, skipped {total_skipped} duplicates.")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sync DeepResearch Agent issues to Linear",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover your team ID
  python sync_to_linear.py --discover --api-key lin_api_xxx

  # Preview all issues (no API writes)
  python sync_to_linear.py --api-key lin_api_xxx --team-id xxx --dry-run

  # Sync only P0 milestone
  python sync_to_linear.py --api-key lin_api_xxx --team-id xxx --milestone P0

  # Sync everything
  python sync_to_linear.py --api-key lin_api_xxx --team-id xxx
        """,
    )
    parser.add_argument("--api-key", required=True, help="Linear API key (lin_api_...)")
    parser.add_argument("--team-id", help="Linear Team ID")
    parser.add_argument("--discover", action="store_true", help="Discover teams, labels, cycles")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    parser.add_argument("--milestone", help="Sync only a specific milestone (P0, M1-M5)")
    parser.add_argument("--issues-file", default="linear_issues.json", help="Path to issues JSON")

    args = parser.parse_args()

    if args.discover:
        discover(args.api_key)
        return

    if not args.team_id:
        print("❌ --team-id is required for sync. Run --discover first to find it.")
        sys.exit(1)

    sync(
        api_key=args.api_key,
        team_id=args.team_id,
        issues_file=args.issues_file,
        dry_run=args.dry_run,
        milestone_filter=args.milestone,
    )


if __name__ == "__main__":
    main()
