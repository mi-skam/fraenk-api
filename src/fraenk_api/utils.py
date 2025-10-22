"""Utility functions for Fraenk API client."""

import json
import os
from datetime import datetime
from importlib.resources import files
from pathlib import Path


def load_fixture(filename: str) -> dict | list:
    """Load mock data from fixtures directory"""
    fixtures_dir = files("fraenk_api").joinpath("fixtures")
    fixture_file = fixtures_dir.joinpath(filename)

    try:
        fixture_text = fixture_file.read_text(encoding='utf-8')
    except (FileNotFoundError, AttributeError):
        raise FileNotFoundError(f"Fixture not found: {filename}")

    return json.loads(fixture_text)


def load_credentials() -> tuple[str, str]:
    """Load credentials from environment or config files.

    Priority order:
    1. Environment variables (FRAENK_USERNAME, FRAENK_PASSWORD)
    2. ~/.config/fraenk/credentials
    3. ./.env (current directory)

    Returns:
        tuple[str, str]: (username, password)

    Raises:
        SystemExit: If credentials cannot be found or loaded
    """
    # Try environment variables first
    creds = _load_credentials_from_env()
    if creds:
        return creds

    # Try user config file
    creds = _load_credentials_from_user_config()
    if creds:
        return creds

    # Try local .env file
    creds = _load_credentials_from_local_env()
    if creds:
        return creds

    # No credentials found anywhere
    _raise_credentials_not_found_error()


def _load_credentials_from_env() -> tuple[str, str] | None:
    """Load credentials from environment variables.

    Returns:
        tuple[str, str] | None: (username, password) or None if not set
    """
    username = os.getenv("FRAENK_USERNAME")
    password = os.getenv("FRAENK_PASSWORD")

    if username and password:
        return username, password

    return None


def _load_credentials_from_user_config() -> tuple[str, str] | None:
    """Load credentials from ~/.config/fraenk/credentials.

    Returns:
        tuple[str, str] | None: (username, password) or None if file doesn't exist

    Raises:
        SystemExit: If file exists but cannot be read or parsed
    """
    config_path = Path.home() / ".config" / "fraenk" / "credentials"

    if not config_path.exists():
        return None

    try:
        return _parse_credentials_file(config_path)
    except Exception as e:
        raise SystemExit(f"Error loading credentials from {config_path}: {e}") from e


def _load_credentials_from_local_env() -> tuple[str, str] | None:
    """Load credentials from ./.env in current directory.

    Returns:
        tuple[str, str] | None: (username, password) or None if file doesn't exist

    Raises:
        SystemExit: If file exists but cannot be read or parsed
    """
    env_path = Path.cwd() / ".env"

    if not env_path.exists():
        return None

    try:
        return _parse_credentials_file(env_path)
    except Exception as e:
        raise SystemExit(f"Error loading credentials from {env_path}: {e}") from e


def _raise_credentials_not_found_error():
    """Raise SystemExit with helpful error message about missing credentials."""
    raise SystemExit(
        "Error: Credentials not found.\n"
        "Please set credentials using one of:\n"
        "  1. Environment variables: FRAENK_USERNAME and FRAENK_PASSWORD\n"
        f"  2. Config file: {Path.home() / '.config' / 'fraenk' / 'credentials'}\n"
        f"  3. Local file: {Path.cwd() / '.env'}\n"
        "\nFile format:\n"
        "  FRAENK_USERNAME=your_phone_number\n"
        "  FRAENK_PASSWORD=your_password"
    )


def _parse_credentials_file(path: Path) -> tuple[str, str] | None:
    """Parse credentials from a file in KEY=value format.

    Args:
        path: Path to the credentials file

    Returns:
        tuple[str, str] | None: (username, password) or None if incomplete

    Raises:
        ValueError: If file format is invalid
    """
    username = None
    password = None

    with path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse KEY=value
            if '=' not in line:
                raise ValueError(f"Invalid format at line {line_num}: {line}")

            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            if key == "FRAENK_USERNAME":
                username = value
            elif key == "FRAENK_PASSWORD":
                password = value

    # Return only if both credentials found
    if username and password:
        return username, password

    return None


def display_data_consumption(data: dict):
    """Display formatted data consumption information"""
    print("\n" + "=" * 50)
    print("📱 FRAENK DATA CONSUMPTION")
    print("=" * 50)

    customer = data.get("customer", {})
    print(f"Phone: {customer.get('msisdn', 'N/A')}")
    print(f"Contract: {customer.get('contractType', 'N/A')}")

    print("\n" + "-" * 50)

    for pass_info in data.get("passes", []):
        print(f"\n📊 {pass_info.get('passName', 'Unknown')}")
        print(
            f"   Used: {pass_info.get('usedVolume', 'N/A')} / {pass_info.get('initialVolume', 'N/A')}"
        )
        print(f"   Usage: {pass_info.get('percentageConsumption', 0)}%")

        # Convert timestamp to readable date
        expiry = pass_info.get("expiryTimestamp")
        if expiry is not None:
            expiry_date = datetime.fromtimestamp(expiry / 1000)
            print(f"   Expires: {expiry_date.strftime('%Y-%m-%d %H:%M')}")

    print("\n" + "=" * 50)


# ============================================================================
# OUTPUT HELPERS
# ============================================================================

def output_data(data: dict, args):
    """Output data in requested format"""
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        display_data_consumption(data)


def log_info(message: str, args):
    """Log informational message"""
    if not args.json and not args.quiet:
        print(message)


def log_progress(message: str, args):
    """Log progress message"""
    if not args.json:
        print(message)
