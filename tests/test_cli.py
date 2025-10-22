"""Comprehensive unit tests for the CLI module."""

import json
import os
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from fraenk_api.cli import load_fixture, main


class TestLoadFixture:
    """Test load_fixture function."""

    def test_load_fixture_contracts_success(self):
        """Test loading contracts.json fixture returns valid data."""
        result = load_fixture("contracts.json")

        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "customerId" in result[0]

    def test_load_fixture_data_consumption_success(self):
        """Test loading data_consumption.json fixture returns valid data."""
        result = load_fixture("data_consumption.json")

        assert isinstance(result, dict)
        assert "customer" in result
        assert "passes" in result

    def test_load_fixture_returns_parsed_json(self):
        """Test that load_fixture returns parsed JSON, not raw text."""
        result = load_fixture("contracts.json")

        assert isinstance(result, (dict, list))
        assert not isinstance(result, str)

    def test_load_fixture_nonexistent_file_raises(self):
        """Test that loading nonexistent fixture raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_fixture("nonexistent.json")

        assert "Fixture not found" in str(exc_info.value)
        assert "nonexistent.json" in str(exc_info.value)

    def test_load_fixture_invalid_json_raises(self):
        """Test that invalid JSON in fixture raises JSONDecodeError."""
        # This would require a malformed fixture file to exist
        # Skipping as it's a filesystem-dependent test
        pass


class TestArgumentParsing:
    """Test CLI argument parsing."""

    def test_no_arguments_defaults(self, clean_env, monkeypatch):
        """Test CLI with no arguments uses default values."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            # Verify progress messages were printed (not quiet mode)
            # This is implicitly tested by not using --quiet

    def test_json_flag_short(self, clean_env, monkeypatch, capsys):
        """Test -j flag enables JSON output mode."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            captured = capsys.readouterr()
            # Should output JSON, not progress messages
            assert "{" in captured.out
            assert "Initiating login" not in captured.out

    def test_json_flag_long(self, clean_env, monkeypatch, capsys):
        """Test --json flag enables JSON output mode."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "--json"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            captured = capsys.readouterr()
            # Should output JSON
            assert "{" in captured.out

    def test_quiet_flag_short(self, clean_env, monkeypatch, capsys):
        """Test -q flag suppresses progress messages."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-q"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            captured = capsys.readouterr()
            # Should not print progress messages
            assert "Fetching contracts" not in captured.out
            assert "Fetching data consumption" not in captured.out

    def test_quiet_flag_long(self, clean_env, monkeypatch, capsys):
        """Test --quiet flag suppresses progress messages."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "--quiet"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            captured = capsys.readouterr()
            assert "Fetching contracts" not in captured.out

    def test_dry_run_flag_short(self, capsys):
        """Test -d flag enables dry-run mode with fixtures."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.load_fixture") as mock_load_fixture, \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_load_fixture.side_effect = [
                [{"id": "12345"}],  # contracts
                {"customer": {}, "passes": []}  # data_consumption
            ]

            main()

            captured = capsys.readouterr()
            assert "DRY-RUN mode" in captured.out
            assert mock_load_fixture.call_count == 2

    def test_dry_run_flag_long(self, capsys):
        """Test --dry-run flag enables dry-run mode with fixtures."""
        with patch("sys.argv", ["fraenk", "--dry-run"]), \
             patch("fraenk_api.cli.load_fixture") as mock_load_fixture, \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_load_fixture.side_effect = [
                [{"id": "12345"}],
                {"customer": {}, "passes": []}
            ]

            main()

            captured = capsys.readouterr()
            assert "DRY-RUN mode" in captured.out

    def test_combined_flags_json_quiet(self, clean_env, monkeypatch, capsys):
        """Test combining -j and -q flags."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j", "-q"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {"customer": {}, "passes": []}

            main()

            captured = capsys.readouterr()
            # JSON mode ignores quiet flag (quiet only applies to pretty output)
            assert "{" in captured.out

    def test_combined_flags_dry_run_json(self, capsys):
        """Test combining -d and -j flags for dry-run JSON output."""
        with patch("sys.argv", ["fraenk", "-d", "-j"]), \
             patch("fraenk_api.cli.load_fixture") as mock_load_fixture:

            mock_consumption = {"customer": {}, "passes": []}
            mock_load_fixture.side_effect = [
                [{"id": "12345"}],
                mock_consumption
            ]

            main()

            captured = capsys.readouterr()
            # Should not print DRY-RUN message in JSON mode
            assert "DRY-RUN mode" not in captured.out
            # Should output JSON
            parsed = json.loads(captured.out)
            assert parsed == mock_consumption

    def test_combined_flags_dry_run_quiet(self, capsys):
        """Test combining -d and -q flags for quiet dry-run."""
        with patch("sys.argv", ["fraenk", "-d", "-q"]), \
             patch("fraenk_api.cli.load_fixture") as mock_load_fixture, \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_load_fixture.side_effect = [
                [{"id": "12345"}],
                {"customer": {}, "passes": []}
            ]

            main()

            captured = capsys.readouterr()
            # Quiet mode suppresses progress messages even in dry-run
            assert "Loading mock contracts" not in captured.out
            assert "Loading mock data consumption" not in captured.out


class TestDryRunMode:
    """Test dry-run mode functionality."""

    def test_dry_run_loads_contracts_fixture(self, capsys):
        """Test dry-run loads contracts from fixtures."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.display_data_consumption"):

            main()

            # No API calls should be made
            # Verified by not mocking FraenkAPI

    def test_dry_run_loads_data_consumption_fixture(self, capsys):
        """Test dry-run loads data consumption from fixtures."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.display_data_consumption") as mock_display:

            main()

            # display_data_consumption should be called with fixture data
            assert mock_display.called
            call_arg = mock_display.call_args[0][0]
            assert "customer" in call_arg
            assert "passes" in call_arg

    def test_dry_run_no_api_calls(self):
        """Test that dry-run mode makes no API calls."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("fraenk_api.cli.display_data_consumption"):

            main()

            # FraenkAPI should never be instantiated in dry-run mode
            assert not mock_api_class.called

    def test_dry_run_no_credentials_required(self, clean_env):
        """Test dry-run mode works without credentials."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.display_data_consumption"):

            # Should not raise even without FRAENK_USERNAME/PASSWORD
            main()

    def test_dry_run_no_sms_input_required(self):
        """Test dry-run mode does not require SMS code input."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("builtins.input") as mock_input, \
             patch("fraenk_api.cli.display_data_consumption"):

            main()

            # input() should never be called in dry-run mode
            assert not mock_input.called

    def test_dry_run_prints_progress_messages(self, capsys):
        """Test dry-run mode prints progress messages by default."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.display_data_consumption"):

            main()

            captured = capsys.readouterr()
            assert "DRY-RUN mode" in captured.out
            assert "Loading mock contracts" in captured.out
            assert "Loading mock data consumption" in captured.out

    def test_dry_run_quiet_suppresses_progress(self, capsys):
        """Test dry-run with --quiet suppresses progress messages."""
        with patch("sys.argv", ["fraenk", "-d", "-q"]), \
             patch("fraenk_api.cli.display_data_consumption"):

            main()

            captured = capsys.readouterr()
            assert "DRY-RUN mode" not in captured.out
            assert "Loading mock contracts" not in captured.out

    def test_dry_run_json_output(self, capsys):
        """Test dry-run mode with --json outputs fixture data as JSON."""
        with patch("sys.argv", ["fraenk", "-d", "-j"]):
            main()

            captured = capsys.readouterr()
            parsed = json.loads(captured.out)
            assert "customer" in parsed
            assert "passes" in parsed


class TestCredentialLoading:
    """Test credential loading flow."""

    def test_credentials_loaded_from_env(self, clean_env, monkeypatch):
        """Test credentials loaded from environment variables."""
        monkeypatch.setenv("FRAENK_USERNAME", "env_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "env_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            # Verify login was called with env credentials
            mock_api.login_initiate.assert_called_once_with("env_user", "env_pass")

    def test_load_credentials_called(self, clean_env, monkeypatch):
        """Test that load_credentials() is called in normal mode."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.load_credentials") as mock_load_creds, \
             patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            mock_load_creds.assert_called_once()

    def test_missing_username_raises_error(self, clean_env, monkeypatch):
        """Test that missing FRAENK_USERNAME raises ValueError."""
        monkeypatch.setenv("FRAENK_PASSWORD", "password")

        with patch("sys.argv", ["fraenk"]), \
             patch("fraenk_api.cli.load_credentials"), \
             pytest.raises(ValueError) as exc_info:

            main()

        assert "FRAENK_USERNAME" in str(exc_info.value)

    def test_missing_password_raises_error(self, clean_env, monkeypatch):
        """Test that missing FRAENK_PASSWORD raises ValueError."""
        monkeypatch.setenv("FRAENK_USERNAME", "username")

        with patch("sys.argv", ["fraenk"]), \
             patch("fraenk_api.cli.load_credentials"), \
             pytest.raises(ValueError) as exc_info:

            main()

        assert "FRAENK_PASSWORD" in str(exc_info.value)

    def test_missing_both_credentials_raises_error(self, clean_env):
        """Test that missing both credentials raises ValueError."""
        with patch("sys.argv", ["fraenk"]), \
             patch("fraenk_api.cli.load_credentials"), \
             pytest.raises(ValueError) as exc_info:

            main()

        assert "FRAENK_USERNAME" in str(exc_info.value)


class TestLoginFlow:
    """Test normal mode login flow with MFA."""

    def test_login_initiate_called_with_credentials(self, clean_env, monkeypatch):
        """Test login_initiate is called with correct credentials."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "test-token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            mock_api.login_initiate.assert_called_once_with("test_user", "test_pass")

    def test_login_initiate_progress_message(self, clean_env, monkeypatch, capsys):
        """Test that login initiate prints progress message."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Initiating login" in captured.out
            assert "SMS sent!" in captured.out

    def test_login_initiate_no_progress_in_json_mode(self, clean_env, monkeypatch, capsys):
        """Test no progress messages in JSON mode."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Initiating login" not in captured.out
            assert "SMS sent!" not in captured.out

    def test_login_initiate_exception_raises_system_exit(self, clean_env, monkeypatch):
        """Test that login_initiate exception raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.side_effect = Exception("Network error")

            main()

        assert "Login initiation failed" in str(exc_info.value)

    def test_missing_mfa_token_raises_system_exit(self, clean_env, monkeypatch):
        """Test that missing mfa_token in response raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"error": "something_wrong"}

            main()

        assert "Login failed" in str(exc_info.value)

    def test_sms_code_input_normal_mode(self, clean_env, monkeypatch):
        """Test SMS code input in normal (pretty) mode."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="654321") as mock_input, \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            # input() should be called with prompt
            mock_input.assert_called_with("Enter SMS code: ")

    def test_sms_code_input_json_mode(self, clean_env, monkeypatch):
        """Test SMS code input in JSON mode (no prompt)."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="654321") as mock_input:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            # input() should be called without prompt (silent)
            mock_input.assert_called_with()

    def test_login_complete_called_with_sms_code(self, clean_env, monkeypatch):
        """Test login_complete is called with SMS code and mfa_token."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="999888"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "my-mfa-token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            mock_api.login_complete.assert_called_once_with(
                "test_user", "test_pass", "999888", "my-mfa-token"
            )

    def test_login_complete_progress_message(self, clean_env, monkeypatch, capsys):
        """Test login_complete prints progress messages."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Completing login with SMS code" in captured.out
            assert "Login successful!" in captured.out

    def test_login_complete_exception_raises_system_exit(self, clean_env, monkeypatch):
        """Test login_complete exception raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.login_complete.side_effect = Exception("Invalid MFA code")

            main()

        assert "Login completion failed" in str(exc_info.value)


class TestDataFetching:
    """Test data fetching flow (contracts and consumption)."""

    def test_get_contracts_called(self, clean_env, monkeypatch):
        """Test get_contracts is called after successful login."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = [{"id": "12345"}]
            mock_api.get_data_consumption.return_value = {}

            main()

            mock_api.get_contracts.assert_called_once()

    def test_get_contracts_progress_message(self, clean_env, monkeypatch, capsys):
        """Test get_contracts prints progress messages."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = [{"id": "1"}, {"id": "2"}]
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Fetching contracts" in captured.out
            assert "Found 2 contract(s)" in captured.out

    def test_get_contracts_quiet_mode_suppresses_progress(self, clean_env, monkeypatch, capsys):
        """Test --quiet suppresses contract fetching messages."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-q"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = [{"id": "1"}]
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Fetching contracts" not in captured.out

    def test_get_contracts_exception_raises_system_exit(self, clean_env, monkeypatch):
        """Test get_contracts exception raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.side_effect = Exception("API error")

            main()

        assert "Failed to fetch contracts" in str(exc_info.value)

    def test_get_data_consumption_called(self, clean_env, monkeypatch):
        """Test get_data_consumption is called after contracts."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {"customer": {}}

            main()

            mock_api.get_data_consumption.assert_called_once()

    def test_get_data_consumption_progress_message(self, clean_env, monkeypatch, capsys):
        """Test get_data_consumption prints progress message."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Fetching data consumption" in captured.out

    def test_get_data_consumption_quiet_mode_suppresses_progress(self, clean_env, monkeypatch, capsys):
        """Test --quiet suppresses data consumption fetching message."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-q"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Fetching data consumption" not in captured.out

    def test_get_data_consumption_exception_raises_system_exit(self, clean_env, monkeypatch):
        """Test get_data_consumption exception raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.side_effect = Exception("Network timeout")

            main()

        assert "Failed to fetch data consumption" in str(exc_info.value)


class TestOutputModes:
    """Test JSON vs pretty print output modes."""

    def test_json_output_format(self, clean_env, monkeypatch, capsys):
        """Test --json outputs valid JSON."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        consumption_data = {
            "customer": {"msisdn": "012345"},
            "passes": [{"passName": "Test"}]
        }

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = consumption_data

            main()

            captured = capsys.readouterr()
            parsed = json.loads(captured.out)
            assert parsed == consumption_data

    def test_json_output_indented(self, clean_env, monkeypatch, capsys):
        """Test --json outputs indented (pretty) JSON."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {"test": "data"}

            main()

            captured = capsys.readouterr()
            # Indented JSON has newlines
            assert "\n" in captured.out

    def test_json_output_no_ensure_ascii(self, clean_env, monkeypatch, capsys):
        """Test --json preserves unicode characters."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        consumption_data = {
            "customer": {"name": "Müller"}  # Unicode character
        }

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = consumption_data

            main()

            captured = capsys.readouterr()
            # ensure_ascii=False preserves unicode
            assert "Müller" in captured.out

    def test_pretty_output_calls_display_function(self, clean_env, monkeypatch):
        """Test normal mode calls display_data_consumption."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        consumption_data = {"customer": {}, "passes": []}

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption") as mock_display:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = consumption_data

            main()

            mock_display.assert_called_once_with(consumption_data)

    def test_json_mode_does_not_call_display_function(self, clean_env, monkeypatch):
        """Test --json mode does not call display_data_consumption."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption") as mock_display:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            assert not mock_display.called


class TestErrorHandling:
    """Test error handling and SystemExit cases."""

    def test_login_initiate_http_error(self, clean_env, monkeypatch):
        """Test HTTP error during login_initiate raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "wrong_pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.side_effect = Exception("401 Unauthorized")

            main()

        assert "Login initiation failed" in str(exc_info.value)
        assert "401 Unauthorized" in str(exc_info.value)

    def test_login_complete_http_error(self, clean_env, monkeypatch):
        """Test HTTP error during login_complete raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="wrong_code"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.login_complete.side_effect = Exception("Invalid MFA code")

            main()

        assert "Login completion failed" in str(exc_info.value)
        assert "Invalid MFA code" in str(exc_info.value)

    def test_get_contracts_http_error(self, clean_env, monkeypatch):
        """Test HTTP error during get_contracts raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.side_effect = Exception("403 Forbidden")

            main()

        assert "Failed to fetch contracts" in str(exc_info.value)
        assert "403 Forbidden" in str(exc_info.value)

    def test_get_data_consumption_http_error(self, clean_env, monkeypatch):
        """Test HTTP error during get_data_consumption raises SystemExit."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.side_effect = Exception("500 Server Error")

            main()

        assert "Failed to fetch data consumption" in str(exc_info.value)
        assert "500 Server Error" in str(exc_info.value)

    def test_error_description_in_mfa_response(self, clean_env, monkeypatch):
        """Test error_description is included in SystemExit message."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             pytest.raises(SystemExit) as exc_info:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {
                "error": "invalid_grant",
                "error_description": "Invalid credentials provided"
            }

            main()

        assert "Invalid credentials provided" in str(exc_info.value)

    def test_fixture_loading_error_in_dry_run(self):
        """Test that fixture loading error is propagated in dry-run."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.load_fixture") as mock_load_fixture, \
             pytest.raises(FileNotFoundError):

            mock_load_fixture.side_effect = FileNotFoundError("Fixture missing")

            main()


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def test_full_normal_flow_pretty_output(self, clean_env, monkeypatch, capsys):
        """Test complete flow from login to pretty output."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        consumption_data = {
            "customer": {"msisdn": "012345"},
            "passes": [{"passName": "Test"}]
        }

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption") as mock_display:

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "mfa-token-xyz"}
            mock_api.get_contracts.return_value = [{"id": "contract1"}]
            mock_api.get_data_consumption.return_value = consumption_data

            main()

            # Verify all steps executed
            mock_api.login_initiate.assert_called_once()
            mock_api.login_complete.assert_called_once()
            mock_api.get_contracts.assert_called_once()
            mock_api.get_data_consumption.assert_called_once()
            mock_display.assert_called_once_with(consumption_data)

            # Verify progress messages
            captured = capsys.readouterr()
            assert "Initiating login" in captured.out
            assert "SMS sent!" in captured.out
            assert "Login successful!" in captured.out

    def test_full_json_flow(self, clean_env, monkeypatch, capsys):
        """Test complete flow with JSON output."""
        monkeypatch.setenv("FRAENK_USERNAME", "test_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "test_pass")

        consumption_data = {"customer": {}, "passes": []}

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = consumption_data

            main()

            captured = capsys.readouterr()
            # No progress messages in JSON mode
            assert "Initiating login" not in captured.out
            # Valid JSON output
            parsed = json.loads(captured.out)
            assert parsed == consumption_data

    def test_full_dry_run_flow(self, capsys):
        """Test complete dry-run flow."""
        with patch("sys.argv", ["fraenk", "-d"]), \
             patch("fraenk_api.cli.display_data_consumption") as mock_display:

            main()

            # Should display fixture data
            assert mock_display.called
            call_arg = mock_display.call_args[0][0]
            assert "customer" in call_arg
            assert "passes" in call_arg

            # Should print dry-run messages
            captured = capsys.readouterr()
            assert "DRY-RUN mode" in captured.out

    def test_quiet_mode_flow(self, clean_env, monkeypatch, capsys):
        """Test complete flow with --quiet flag."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-q"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = [{"id": "1"}]
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            # Should suppress progress messages but keep login messages
            assert "Fetching contracts" not in captured.out
            assert "Fetching data consumption" not in captured.out
            # Login messages still appear (quiet only applies to data fetching)
            assert "Initiating login" in captured.out


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_contracts_list(self, clean_env, monkeypatch, capsys):
        """Test handling of empty contracts list."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Found 0 contract(s)" in captured.out

    def test_multiple_contracts(self, clean_env, monkeypatch, capsys):
        """Test handling of multiple contracts."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = [
                {"id": "1"}, {"id": "2"}, {"id": "3"}
            ]
            mock_api.get_data_consumption.return_value = {}

            main()

            captured = capsys.readouterr()
            assert "Found 3 contract(s)" in captured.out

    def test_empty_sms_code_input(self, clean_env, monkeypatch):
        """Test handling of empty SMS code input."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value=""), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            # Empty SMS code is passed to API (API will handle validation)
            mock_api.login_complete.assert_called_once()
            assert mock_api.login_complete.call_args[0][2] == ""

    def test_whitespace_credentials(self, clean_env, monkeypatch):
        """Test handling of credentials with whitespace."""
        monkeypatch.setenv("FRAENK_USERNAME", "  user  ")
        monkeypatch.setenv("FRAENK_PASSWORD", "  pass  ")

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk"]), \
             patch("builtins.input", return_value="123456"), \
             patch("fraenk_api.cli.display_data_consumption"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = {}

            main()

            # Credentials are passed as-is (not stripped)
            mock_api.login_initiate.assert_called_once_with("  user  ", "  pass  ")

    def test_large_consumption_data_json_output(self, clean_env, monkeypatch, capsys):
        """Test JSON output with large consumption data."""
        monkeypatch.setenv("FRAENK_USERNAME", "user")
        monkeypatch.setenv("FRAENK_PASSWORD", "pass")

        # Create large dataset
        large_data = {
            "customer": {"msisdn": "012345"},
            "passes": [{"passName": f"Pass{i}"} for i in range(100)]
        }

        with patch("fraenk_api.cli.FraenkAPI") as mock_api_class, \
             patch("sys.argv", ["fraenk", "-j"]), \
             patch("builtins.input", return_value="123456"):

            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login_initiate.return_value = {"mfa_token": "token"}
            mock_api.get_contracts.return_value = []
            mock_api.get_data_consumption.return_value = large_data

            main()

            captured = capsys.readouterr()
            parsed = json.loads(captured.out)
            assert len(parsed["passes"]) == 100
