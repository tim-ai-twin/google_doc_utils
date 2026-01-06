#!/usr/bin/env python3
"""Clean up orphaned test resources from Google Drive.

This script finds and deletes test documents and folders that may have been
left behind from failed test runs or incomplete cleanup.

Usage:
    # Dry run - show what would be deleted
    uv run scripts/cleanup_test_resources.py --dry-run

    # Delete resources older than 24 hours
    uv run scripts/cleanup_test_resources.py --older-than 24

    # Show orphaned resources (test resources left in Drive)
    uv run scripts/cleanup_test_resources.py --show-orphaned

    # Delete all matching resources
    uv run scripts/cleanup_test_resources.py
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from extended_google_doc_utils.auth.credential_manager import (
    CredentialManager,
    CredentialSourceDetector,
)

# Test resource name patterns
TEST_PATTERNS = [
    "test-doc-",
    "test-folder-",
    "test-spreadsheet-",
]


def get_credentials() -> Credentials | None:
    """Load Google OAuth credentials.

    Returns:
        Google Credentials object if available, None otherwise
    """
    env_type = CredentialSourceDetector.detect_environment()
    credential_source = CredentialSourceDetector.get_credential_source(env_type)

    manager = CredentialManager(source=credential_source)
    oauth_creds = manager.get_credentials_for_testing()

    if oauth_creds is None:
        return None

    return Credentials(
        token=oauth_creds.access_token,
        refresh_token=oauth_creds.refresh_token,
        token_uri=oauth_creds.token_uri,
        client_id=oauth_creds.client_id,
        client_secret=oauth_creds.client_secret,
        scopes=oauth_creds.scopes,
    )


def search_test_resources(service, pattern: str) -> list[dict]:
    """Search for test resources matching a pattern.

    Args:
        service: Google Drive API service
        pattern: Name pattern to search for (e.g., "test-doc-")

    Returns:
        List of file metadata dicts with id, name, createdTime, mimeType
    """
    results = []
    page_token = None

    while True:
        query = f"name contains '{pattern}' and trashed = false"
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, createdTime, mimeType)",
                pageToken=page_token,
                pageSize=100,
            )
            .execute()
        )

        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return results


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse Google Drive timestamp to datetime.

    Args:
        timestamp_str: ISO format timestamp from Google API

    Returns:
        Timezone-aware datetime object
    """
    # Handle both formats: with and without milliseconds
    try:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        # Try without microseconds
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )


def filter_by_age(resources: list[dict], hours: int) -> list[dict]:
    """Filter resources to only include those older than specified hours.

    Args:
        resources: List of resource metadata dicts
        hours: Minimum age in hours

    Returns:
        Filtered list of resources
    """
    now = datetime.now(timezone.utc)
    filtered = []

    for resource in resources:
        created_time = parse_timestamp(resource["createdTime"])
        age_hours = (now - created_time).total_seconds() / 3600

        if age_hours >= hours:
            resource["age_hours"] = age_hours
            filtered.append(resource)

    return filtered


def format_resource(resource: dict) -> str:
    """Format a resource for display.

    Args:
        resource: Resource metadata dict

    Returns:
        Formatted string for display
    """
    name = resource["name"]
    resource_id = resource["id"]
    created = resource["createdTime"][:10]  # Just the date
    mime_type = resource.get("mimeType", "unknown")

    # Determine type from mime type
    if "document" in mime_type:
        rtype = "doc"
    elif "folder" in mime_type:
        rtype = "folder"
    elif "spreadsheet" in mime_type:
        rtype = "sheet"
    else:
        rtype = "file"

    age_str = ""
    if "age_hours" in resource:
        hours = resource["age_hours"]
        if hours >= 24:
            age_str = f" ({hours / 24:.1f} days old)"
        else:
            age_str = f" ({hours:.1f} hours old)"

    return f"  [{rtype}] {name} (created {created}){age_str}\n         ID: {resource_id}"


def format_age_string(hours: float) -> str:
    """Format age in hours to human-readable string.

    Args:
        hours: Age in hours

    Returns:
        Human-readable age string (e.g., "2 days ago", "3 hours ago")
    """
    if hours >= 48:
        days = int(hours / 24)
        return f"{days} days ago"
    elif hours >= 24:
        return "1 day ago"
    elif hours >= 2:
        return f"{int(hours)} hours ago"
    elif hours >= 1:
        return "1 hour ago"
    else:
        minutes = int(hours * 60)
        return f"{minutes} minutes ago"


def format_orphaned_list(resources: list[dict]) -> str:
    """Format orphaned resources as a numbered list.

    Args:
        resources: List of resource metadata dicts with age_hours

    Returns:
        Formatted string with numbered list
    """
    if not resources:
        return "No orphaned resources found."

    lines = [f"Found {len(resources)} orphaned resource(s):"]

    for i, resource in enumerate(resources, 1):
        name = resource["name"]
        age_hours = resource.get("age_hours", 0)
        age_str = format_age_string(age_hours)
        lines.append(f"{i}. {name} (created {age_str})")

    return "\n".join(lines)


def delete_resource(service, resource_id: str) -> bool:
    """Delete a resource from Google Drive.

    Args:
        service: Google Drive API service
        resource_id: ID of resource to delete

    Returns:
        True if deletion succeeded, False otherwise
    """
    try:
        service.files().delete(fileId=resource_id).execute()
        return True
    except Exception as e:
        print(f"    Error deleting {resource_id}: {e}")
        return False


def main():
    """Run the cleanup script."""
    parser = argparse.ArgumentParser(
        description="Clean up orphaned test resources from Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/cleanup_test_resources.py --dry-run
      Show what would be deleted without actually deleting

  uv run scripts/cleanup_test_resources.py --older-than 24
      Delete only resources older than 24 hours

  uv run scripts/cleanup_test_resources.py --show-orphaned
      List orphaned test resources without deleting

  uv run scripts/cleanup_test_resources.py
      Delete all matching test resources
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--show-orphaned",
        action="store_true",
        help="Display orphaned resources (test resources left in Drive) without deleting",
    )
    parser.add_argument(
        "--older-than",
        type=int,
        metavar="HOURS",
        help="Only delete resources older than specified hours",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        help="Additional name pattern to search for (can be used multiple times)",
    )

    args = parser.parse_args()

    # Get credentials
    print("\nLoading credentials...")
    credentials = get_credentials()

    if credentials is None:
        print("Error: No credentials available.")
        print("Run 'uv run scripts/bootstrap_oauth.py' to set up credentials.")
        sys.exit(1)

    # Build Drive service
    service = build("drive", "v3", credentials=credentials)

    # Collect patterns to search
    patterns = list(TEST_PATTERNS)
    if args.pattern:
        patterns.extend(args.pattern)

    # Search for test resources
    print(f"\nSearching for test resources...")
    all_resources = []

    for pattern in patterns:
        resources = search_test_resources(service, pattern)
        all_resources.extend(resources)

    # Deduplicate by ID
    seen_ids = set()
    unique_resources = []
    for resource in all_resources:
        if resource["id"] not in seen_ids:
            seen_ids.add(resource["id"])
            unique_resources.append(resource)

    # Filter by age if specified
    if args.older_than:
        unique_resources = filter_by_age(unique_resources, args.older_than)
        print(f"Filtered to resources older than {args.older_than} hours")

    # Calculate age for all resources if not already done
    if not args.older_than:
        now = datetime.now(timezone.utc)
        for resource in unique_resources:
            if "age_hours" not in resource:
                created_time = parse_timestamp(resource["createdTime"])
                resource["age_hours"] = (now - created_time).total_seconds() / 3600

    # Display results
    if not unique_resources:
        print("\nNo test resources found matching the search criteria.")
        sys.exit(0)

    # Show orphaned mode - display numbered list and exit
    if args.show_orphaned:
        print()
        print(format_orphaned_list(unique_resources))
        sys.exit(0)

    print(f"\nFound {len(unique_resources)} test resource(s):\n")
    for resource in unique_resources:
        print(format_resource(resource))
        print()

    # Dry run - just show what would be deleted
    if args.dry_run:
        print("-" * 60)
        print("DRY RUN - No resources were deleted.")
        print(f"Run without --dry-run to delete {len(unique_resources)} resource(s).")
        sys.exit(0)

    # Confirm deletion
    print("-" * 60)
    response = input(f"Delete {len(unique_resources)} resource(s)? [y/N]: ").strip().lower()

    if response != "y":
        print("Aborted.")
        sys.exit(0)

    # Delete resources
    print("\nDeleting resources...")
    succeeded = 0
    failed = 0

    for resource in unique_resources:
        print(f"  Deleting {resource['name']}...", end=" ")
        if delete_resource(service, resource["id"]):
            print("OK")
            succeeded += 1
        else:
            print("FAILED")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Cleanup complete: {succeeded} deleted, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
