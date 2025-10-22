"""Shared pytest fixtures for the Fraenk API test suite."""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock
import pytest


@pytest.fixture
def mock_mfa_response() -> Dict[str, Any]:
    """Standard MFA response from login_initiate."""
    return {
        "error": "mfa_required",
        "error_description": "Multi-factor authentication is required",
        "mfa_token": "test-mfa-token-12345"
    }


@pytest.fixture
def mock_jwt_token() -> str:
    """Valid JWT for testing with customer ID in sub field."""
    # Create a proper JWT structure with header.payload.signature
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "sub": "f:uuid:7555659511",
        "iat": 1234567890,
        "exp": 1234567890,
        "iss": "fraenk"
    }

    # Base64 encode the parts (without padding for JWT standard)
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "fake-signature"

    return f"{header_b64}.{payload_b64}.{signature}"


@pytest.fixture
def mock_login_response(mock_jwt_token) -> Dict[str, Any]:
    """Standard successful login response with tokens."""
    return {
        "access_token": mock_jwt_token,
        "refresh_token": "refresh-token-67890",
        "token_type": "Bearer",
        "expires_in": 3600
    }


@pytest.fixture
def mock_contracts_response() -> list:
    """Mock contracts API response."""
    return [
        {
            "id": "12345678",
            "customerId": "7555659511",
            "contractType": "POST_PAID",
            "status": "ACTIVE",
            "msisdn": "0151 - 29489521"
        },
        {
            "id": "87654321",
            "customerId": "7555659511",
            "contractType": "POST_PAID",
            "status": "INACTIVE",
            "msisdn": "0151 - 29489522"
        }
    ]


@pytest.fixture
def mock_consumption_response() -> Dict[str, Any]:
    """Mock data consumption response."""
    return {
        "customer": {
            "msisdn": "0151 - 29489521",
            "contractType": "POST_PAID"
        },
        "passes": [
            {
                "passName": "Vertragsvolumen",
                "type": "INCLUSIVE",
                "usedVolume": "6,47 GB",
                "usedBytes": 6952624056,
                "initialVolume": "25 GB",
                "initialVolumeBytes": 26843545600,
                "percentageConsumption": 26,
                "expiryTimestamp": 1761951599000
            }
        ],
        "bookableDataPassesAvailable": True
    }


@pytest.fixture
def temp_env_file(tmp_path) -> Path:
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "FRAENK_USERNAME=0151123456789\n"
        "FRAENK_PASSWORD=test_password123\n"
    )
    return env_file


@pytest.fixture
def temp_config_file(tmp_path) -> Path:
    """Create a temporary config file for testing."""
    config_dir = tmp_path / ".config" / "fraenk"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "credentials"
    config_file.write_text(
        "FRAENK_USERNAME=0151987654321\n"
        "FRAENK_PASSWORD=config_password456\n"
    )
    return config_file


@pytest.fixture
def mock_api_headers() -> Dict[str, str]:
    """Expected base headers for API requests."""
    return {
        "X-Tenant": "fraenk",
        "X-App-OS": "Android",
        "X-App-Device": "Python-Client",
        "X-App-Device-Vendor": "Python",
        "X-App-OS-Version": "13",
        "X-App-Version": "1.13.9"
    }


@pytest.fixture
def fixture_contracts() -> list:
    """Load actual contracts fixture data."""
    fixture_path = Path(__file__).parent.parent / "src" / "fraenk_api" / "fixtures" / "contracts.json"
    if fixture_path.exists():
        return json.loads(fixture_path.read_text())
    # Fallback if fixture doesn't exist
    return [{
        "id": "12345678",
        "customerId": "12345761",
        "contractType": "POST_PAID",
        "status": "ACTIVE",
        "msisdn": "0151 - 29489521"
    }]


@pytest.fixture
def fixture_consumption() -> Dict[str, Any]:
    """Load actual data consumption fixture data."""
    fixture_path = Path(__file__).parent.parent / "src" / "fraenk_api" / "fixtures" / "data_consumption.json"
    if fixture_path.exists():
        return json.loads(fixture_path.read_text())
    # Fallback if fixture doesn't exist
    return {
        "customer": {
            "msisdn": "01234 - 567890",
            "contractType": "POST_PAID"
        },
        "passes": [{
            "passName": "Vertragsvolumen",
            "type": "INCLUSIVE",
            "usedVolume": "6,47 GB",
            "usedBytes": 6952624056,
            "initialVolume": "25 GB",
            "initialVolumeBytes": 26843545600,
            "percentageConsumption": 26,
            "expiryTimestamp": 1761951599000
        }],
        "bookableDataPassesAvailable": True
    }


@pytest.fixture
def clean_env(monkeypatch):
    """Remove Fraenk environment variables and isolate os.environ modifications."""
    # Save original environment state
    original_env = os.environ.copy()

    # Remove Fraenk credentials from the test environment
    monkeypatch.delenv("FRAENK_USERNAME", raising=False)
    monkeypatch.delenv("FRAENK_PASSWORD", raising=False)

    yield monkeypatch

    # Restore original environment after test
    for key in list(os.environ.keys()):
        if key.startswith("FRAENK_"):
            if key in original_env:
                os.environ[key] = original_env[key]
            else:
                os.environ.pop(key, None)


@pytest.fixture
def mock_stdin(monkeypatch):
    """Mock stdin for SMS code input."""
    from io import StringIO
    mock_input = StringIO("123456\n")
    monkeypatch.setattr('sys.stdin', mock_input)
    return mock_input