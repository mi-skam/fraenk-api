"""Command-line interface for Fraenk API client."""

import argparse
import json
import os
from pathlib import Path

from fraenk_api.client import FraenkAPI
from fraenk_api.utils import display_data_consumption, load_env_file


def load_fixture(filename: str) -> dict:
    """Load mock data from fixtures directory"""
    fixture_path = Path.cwd() / "fixtures" / filename
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    with open(fixture_path) as f:
        return json.load(f)


def main():
    """Main function to demonstrate API usage"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Fraenk mobile data consumption tracker"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output raw JSON to stdout (pipeable)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress messages (only applies to pretty output)"
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Use mock data from fixtures/ (no API calls, no SMS required)"
    )
    args = parser.parse_args()

    # Dry-run mode: use fixtures instead of API calls
    if args.dry_run:
        if not args.json and not args.quiet:
            print("Running in DRY-RUN mode (using fixtures)")
            print("Loading mock contracts...")
        contracts = load_fixture("contracts.json")
        if not args.json and not args.quiet:
            print(f"Found {len(contracts)} contract(s)")
            print("Loading mock data consumption...")
        data = load_fixture("data_consumption.json")
    else:
        # Normal mode: use real API calls
        # Load .env file if it exists
        load_env_file()

        # Get credentials from environment variables
        username = os.getenv("FRAENK_USERNAME")
        password = os.getenv("FRAENK_PASSWORD")

        if not username:
            raise ValueError("FRAENK_USERNAME environment variable must be set")
        if not password:
            raise ValueError("FRAENK_PASSWORD environment variable must be set")

        api = FraenkAPI()

        # Login Step 1: Request SMS code
        if not args.json:
            print("Initiating login (MFA SMS will be sent)...")
        mfa_response = api.login_initiate(username, password)
        if not args.json:
            print(f"MFA response: {mfa_response.get('error_description', 'SMS sent!')}")
        mfa_token = mfa_response["mfa_token"]

        # Enter SMS code
        sms_code = input("Enter SMS code: ")

        # Login Step 2: Complete login with SMS code
        if not args.json:
            print("Completing login with SMS code...")
        api.login_complete(username, password, sms_code, mfa_token)
        if not args.json:
            print("Login successful!")

        # Fetch contracts
        if not args.json and not args.quiet:
            print("\nFetching contracts...")
        contracts = api.get_contracts()
        if not args.json and not args.quiet:
            print(f"Found {len(contracts)} contract(s)")

        # Fetch data consumption
        if not args.json and not args.quiet:
            print("Fetching data consumption...")
        data = api.get_data_consumption()

    # Output based on mode
    if args.json:
        # JSON mode: only print raw JSON
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        # Pretty mode: display formatted data consumption
        display_data_consumption(data)


if __name__ == "__main__":
    main()
