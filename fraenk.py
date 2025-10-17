import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


class FraenkAPI:
    BASE_URL = "https://app.fraenk.de/fraenk-rest-service/app/v13"

    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.contract_id: Optional[str] = None

    def _base_headers(self):
        """Standard Headers ohne Auth"""
        return {
            "X-Tenant": "fraenk",
            "X-App-OS": "Android",
            "X-App-Device": "Python-Client",
            "X-App-Device-Vendor": "Python",
            "X-App-OS-Version": "13",
            "X-App-Version": "1.13.9",
        }

    def _auth_headers(self):
        """Headers mit Bearer Token"""
        headers = self._base_headers()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def login_initiate(self, username: str, password: str) -> dict:
        """Schritt 1: Login initiieren - SMS Code wird verschickt (MFA)"""
        headers = self._base_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        response = requests.post(
            f"{self.BASE_URL}/login",
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "app",
            },
            headers=headers,
        )

        # 401 with mfa_required is expected for MFA flow
        data = response.json()
        if response.status_code == 401 and data.get("error") == "mfa_required":
            return data

        # For other errors, raise exception
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Response body: {response.text}")
            response.raise_for_status()

        return data

    def login_complete(
        self, username: str, password: str, mtan: str, mfa_token: str
    ) -> dict:
        """Schritt 2: Login mit SMS-Code abschließen (MFA)"""
        headers = self._base_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        response = requests.post(
            f"{self.BASE_URL}/login-with-mfa",
            data={
                "username": username,
                "password": password,
                "mtan": mtan,
                "mfa_token": mfa_token,
            },
            headers=headers,
        )

        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Response body: {response.text}")

        response.raise_for_status()

        auth = response.json()
        self.access_token = auth["access_token"]
        self.refresh_token = auth["refresh_token"]

        # Customer ID aus dem JWT Token extrahieren (ohne Library)
        # JWT format: header.payload.signature - we only need the payload
        payload = auth["access_token"].split(".")[1]
        # Add padding if needed for base64 decoding
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        raw_customer_id = decoded.get("sub")

        # Extract numeric customer ID from format like "f:uuid:7555659511"
        if ":" in raw_customer_id:
            self.customer_id = raw_customer_id.split(":")[-1]
        else:
            self.customer_id = raw_customer_id

        return auth

    def get_contracts(self) -> list:
        """Alle Verträge abrufen"""
        response = requests.get(
            f"{self.BASE_URL}/customers/{self.customer_id}/contracts",
            headers=self._auth_headers(),
        )
        response.raise_for_status()

        contracts = response.json()
        if contracts:
            self.contract_id = contracts[0]["id"]

        return contracts

    def get_data_consumption(self, use_cache: bool = False) -> dict:
        """Datenverbrauch abrufen"""
        headers = self._auth_headers()
        if not use_cache:
            headers["Cache-Control"] = "no-cache"

        response = requests.get(
            f"{self.BASE_URL}/customers/{self.customer_id}/contracts/{self.contract_id}/dataconsumption",
            headers=headers,
        )
        response.raise_for_status()

        return response.json()


def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def save_json_export(data: dict) -> str:
    """Save data consumption to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"fraenk-api-{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filename


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


def main():
    """Main function to demonstrate API usage"""
    # Parse command line arguments
    save_json = "--json" in sys.argv

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

    # Login Schritt 1: SMS Code anfordern
    print("Initiating login (MFA SMS will be sent)...")
    mfa_response = api.login_initiate(username, password)
    print(f"MFA response: {mfa_response.get('error_description', 'SMS sent!')}")
    mfa_token = mfa_response["mfa_token"]

    # SMS-Code eingeben
    sms_code = input("Enter SMS code: ")

    # Login Schritt 2: Mit SMS-Code einloggen
    print("Completing login with SMS code...")
    api.login_complete(username, password, sms_code, mfa_token)
    print("Login successful!")

    # Contracts abrufen
    print("\nFetching contracts...")
    contracts = api.get_contracts()
    print(f"Found {len(contracts)} contract(s)")

    # Datenverbrauch abrufen
    print("Fetching data consumption...")
    data = api.get_data_consumption()

    # Save JSON if requested
    if save_json:
        filename = save_json_export(data)
        print(f"\n✅ Saved to {filename}")

    # Display formatted data consumption
    display_data_consumption(data)


if __name__ == "__main__":
    main()
