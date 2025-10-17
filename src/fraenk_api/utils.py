"""Utility functions for Fraenk API client."""

import os
from datetime import datetime
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


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
