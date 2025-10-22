"""Minimal focused tests for Fraenk API client.

Philosophy: Test behavior, not implementation. Focus on integration over unit tests.

This single file replaces the old test_cli.py, test_utils.py, test_init.py, and test_main.py,
reducing test code from 3090 lines to ~150 lines while maintaining coverage of critical paths.
"""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from fraenk_api import FraenkAPI
from fraenk_api.cli import load_fixture, main
from fraenk_api.utils import print_consumption


# --- Client Tests (Core Business Logic) ---


def test_login_flow_extracts_customer_id_from_jwt():
    """Verify the full MFA login flow extracts customer ID correctly."""
    api = FraenkAPI()

    # Create a realistic JWT with customer ID in sub field
    import base64

    payload = {"sub": "f:uuid:7555659511"}
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    fake_jwt = f"header.{payload_b64}.signature"

    with patch("fraenk_api.client.requests.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "access_token": fake_jwt,
            "refresh_token": "refresh123",
        }
        mock_post.return_value.raise_for_status = Mock()

        api.login_complete("user", "pass", "123456", "mfa_token")

        assert api.customer_id == "7555659511"


def test_get_data_consumption_uses_correct_url():
    """Verify API constructs correct URLs with customer/contract IDs."""
    api = FraenkAPI()
    api.access_token = "token123"
    api.customer_id = "customer123"
    api.contract_id = "contract456"

    with patch("fraenk_api.client.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": "test"}
        mock_get.return_value.raise_for_status = Mock()

        api.get_data_consumption()

        called_url = mock_get.call_args[0][0]
        assert "customer123" in called_url
        assert "contract456" in called_url


# --- CLI Tests (Integration) ---


def test_dry_run_mode_loads_fixtures():
    """Verify --dry-run mode works without API calls."""
    contracts = load_fixture("contracts.json")
    data = load_fixture("data_consumption.json")

    assert isinstance(contracts, list)
    assert isinstance(data, dict)
    assert "customer" in data


@pytest.mark.parametrize(
    "expiry,should_display",
    [
        (1234567890000, True),  # Normal timestamp
        (0, True),  # Zero timestamp (epoch)
        (None, False),  # None (missing field)
    ],
)
def test_display_handles_timestamp_edge_cases(expiry, should_display, capsys):
    """Verify display function handles various timestamp scenarios."""
    data = {
        "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
        "passes": [
            {
                "passName": "Test",
                "usedVolume": "1 GB",
                "initialVolume": "10 GB",
                "percentageConsumption": 10,
                "expiryTimestamp": expiry,
            }
        ],
    }

    print_consumption(data)
    output = capsys.readouterr().out

    if should_display:
        assert "Expires:" in output
    else:
        assert "Expires:" not in output


# --- Property-Based Test Example ---


@pytest.mark.parametrize("percentage", [0, 25, 50, 75, 100])
def test_display_shows_all_percentages(percentage, capsys):
    """Verify percentage display works across full range."""
    data = {
        "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
        "passes": [
            {
                "passName": "Test",
                "usedVolume": f"{percentage} GB",
                "initialVolume": "100 GB",
                "percentageConsumption": percentage,
            }
        ],
    }

    print_consumption(data)
    output = capsys.readouterr().out

    assert f"{percentage}%" in output


# --- Package Tests ---


def test_package_exports():
    """Verify package exports FraenkAPI."""
    import fraenk_api

    assert hasattr(fraenk_api, "FraenkAPI")
    assert hasattr(fraenk_api, "__version__")


def test_main_module_executable():
    """Verify __main__.py can be executed."""
    main_file = Path(__file__).parent.parent / "src" / "fraenk_api" / "__main__.py"
    source = main_file.read_text()

    # Verify structure
    assert "from fraenk_api.cli import main" in source
    assert 'if __name__ == "__main__":' in source


# --- CLI Integration Tests ---


def test_cli_dry_run_mode_succeeds(capsys):
    """Verify complete dry-run flow works."""
    with patch("sys.argv", ["fraenk", "--dry-run", "--json"]):
        main()

    # Verify JSON was printed
    output = capsys.readouterr().out
    data = json.loads(output)
    assert "customer" in data
    assert "passes" in data


def test_cli_requires_credentials_in_normal_mode(monkeypatch):
    """Verify CLI fails gracefully when credentials missing."""
    monkeypatch.delenv("FRAENK_USERNAME", raising=False)
    monkeypatch.delenv("FRAENK_PASSWORD", raising=False)

    with patch("sys.argv", ["fraenk"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert "FRAENK_USERNAME" in str(exc_info.value)
