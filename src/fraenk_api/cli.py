"""Command-line interface for Fraenk API client."""

import argparse

from fraenk_api.client import FraenkAPI
from fraenk_api.utils import (
    load_credentials,
    load_fixture,
    log_info,
    log_progress,
    print_consumption_as_json,
    print_consumption,
)


def main():
    """Main CLI entry point"""
    args = parse_args()
    data = run(args)

    if args.json:
        print_consumption_as_json(data)
    else:
        print_consumption(data)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fraenk mobile data consumption tracker"
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="Output raw JSON to stdout (pipeable)"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages (only applies to pretty output)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Use mock data from fixtures/ (no API calls, no SMS required)",
    )
    return parser.parse_args()


def run(args) -> dict:
    """Execute workflow (dry-run with fixtures or real API calls)"""
    if args.dry_run:
        log_info("Running in DRY-RUN mode (using fixtures)", args)
        api = None
    else:
        api = authenticate(args)

    contracts = fetch_contracts(api, args)
    log_info(f"Found {len(contracts)} contract(s)", args)

    data = fetch_data_consumption(api, args)
    return data


def authenticate(args) -> FraenkAPI:
    """Authenticate and return API client"""
    username, password = load_credentials()
    api = FraenkAPI()
    perform_mfa_login(api, username, password, args)
    return api


def fetch_contracts(api: FraenkAPI | None, args) -> list:
    """Fetch contracts from API or fixtures"""
    if api is None:
        log_info("Loading mock contracts...", args)
        contract = load_fixture("contracts.json")
        return [contract]

    log_info("\nFetching contracts...", args)
    try:
        return api.get_contracts()
    except Exception as e:
        raise SystemExit(f"Failed to fetch contracts: {e}") from e


def fetch_data_consumption(api: FraenkAPI | None, args) -> dict:
    """Fetch data consumption from API or fixtures"""
    if api is None:
        log_info("Loading mock data consumption...", args)
        return load_fixture("data_consumption.json")

    log_info("Fetching data consumption...", args)
    try:
        return api.get_data_consumption()
    except Exception as e:
        raise SystemExit(f"Failed to fetch data consumption: {e}") from e


def perform_mfa_login(api: FraenkAPI, username: str, password: str, args):
    """Handle two-step MFA login flow"""
    # Login Step 1: Initiate (send SMS)
    log_progress("Initiating login (MFA SMS will be sent)...", args)
    try:
        mfa_response = api.login_initiate(username, password)
    except Exception as e:
        raise SystemExit(f"Login initiation failed: {e}") from e

    log_progress("SMS sent!", args)

    mfa_token = mfa_response.get("mfa_token")
    if not mfa_token:
        raise SystemExit(
            f"Login failed: {mfa_response.get('error_description', 'No MFA token received')}"
        )

    # Get SMS code from user
    sms_code = prompt_sms_code(args)

    # Login Step 2: Complete with SMS code
    log_progress("Completing login with SMS code...", args)
    try:
        api.login_complete(username, password, sms_code, mfa_token)
    except Exception as e:
        raise SystemExit(f"Login completion failed: {e}") from e

    log_progress("Login successful!", args)


def prompt_sms_code(args) -> str:
    """Prompt user for SMS code (silent in JSON mode)"""
    if args.json:
        return input()
    return input("Enter SMS code: ")


if __name__ == "__main__":
    main()
