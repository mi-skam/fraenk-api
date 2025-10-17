"""Fraenk API client for mobile data consumption tracking."""

import base64
import json
from typing import Optional

import requests


class FraenkAPI:
    """Client for interacting with the Fraenk mobile API."""

    BASE_URL = "https://app.fraenk.de/fraenk-rest-service/app/v13"

    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.contract_id: Optional[str] = None

    def _base_headers(self):
        """Standard headers without authentication"""
        return {
            "X-Tenant": "fraenk",
            "X-App-OS": "Android",
            "X-App-Device": "Python-Client",
            "X-App-Device-Vendor": "Python",
            "X-App-OS-Version": "13",
            "X-App-Version": "1.13.9",
        }

    def _auth_headers(self):
        """Headers with Bearer token"""
        headers = self._base_headers()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def login_initiate(self, username: str, password: str) -> dict:
        """Step 1: Initiate login - SMS code will be sent (MFA)"""
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
        """Step 2: Complete login with SMS code (MFA)"""
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
        """Fetch all contracts"""
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
        """Fetch data consumption"""
        headers = self._auth_headers()
        if not use_cache:
            headers["Cache-Control"] = "no-cache"

        response = requests.get(
            f"{self.BASE_URL}/customers/{self.customer_id}/contracts/{self.contract_id}/dataconsumption",
            headers=headers,
        )
        response.raise_for_status()

        return response.json()
