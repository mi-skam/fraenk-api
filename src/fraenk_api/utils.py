"""Utility functions for Fraenk API client."""

import os
from datetime import datetime
from pathlib import Path


def load_credentials():
    """Load credentials with fallback chain.

    Priority (highest to lowest):
    1. Environment variables (already set)
    2. Config file at ~/.config/fraenk/credentials
    3. .env file in current directory

    Does not fail - just loads what's available.
    Actual validation happens in cli.py when checking for username/password.
    """
    credentials = {}

    # Load .env from current directory (lowest priority)
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        credentials.update(_parse_env_file(env_file))

    # Load config file (higher priority, overrides .env)
    config_path = Path.home() / ".config" / "fraenk" / "credentials"
    if config_path.exists():
        credentials.update(_parse_env_file(config_path))

    # Set in os.environ only if not already present (env vars have highest priority)
    for key, value in credentials.items():
        if key not in os.environ:
            os.environ[key] = value


def _parse_env_file(file_path: Path) -> dict:
    """Parse KEY=VALUE pairs from a file.

    Args:
        file_path: Path to the credentials file

    Returns:
        Dictionary of key-value pairs
    """
    credentials = {}
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                # Remove surrounding quotes if present
                if value and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                credentials[key.strip()] = value
    return credentials


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
        if expiry:
            expiry_date = datetime.fromtimestamp(expiry / 1000)
            print(f"   Expires: {expiry_date.strftime('%Y-%m-%d %H:%M')}")

    print("\n" + "=" * 50)
