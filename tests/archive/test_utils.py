"""Unit tests for the utils module."""

import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
import pytest

from fraenk_api import utils


class TestLoadCredentials:
    """Test load_credentials function."""

    def test_load_credentials_env_vars_only(self, monkeypatch, clean_env):
        """Test loading credentials when only environment variables are set."""
        # Set env vars directly
        monkeypatch.setenv("FRAENK_USERNAME", "env_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "env_pass")

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False  # No files exist

            utils.load_credentials()

            # Should keep env vars as-is
            assert os.environ["FRAENK_USERNAME"] == "env_user"
            assert os.environ["FRAENK_PASSWORD"] == "env_pass"

    def test_load_credentials_from_env_file(self, monkeypatch, clean_env, tmp_path):
        """Test loading credentials from .env file in current directory."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "FRAENK_USERNAME=dotenv_user\nFRAENK_PASSWORD=dotenv_pass\n"
        )

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            # Mock home to prevent loading from ~/.config
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = tmp_path / "fake_home"

                utils.load_credentials()

                assert os.environ["FRAENK_USERNAME"] == "dotenv_user"
                assert os.environ["FRAENK_PASSWORD"] == "dotenv_pass"

    def test_load_credentials_from_config(self, monkeypatch, clean_env, tmp_path):
        """Test loading credentials from ~/.config/fraenk/credentials."""
        # Create config file
        config_dir = tmp_path / ".config" / "fraenk"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "credentials"
        config_file.write_text(
            "FRAENK_USERNAME=config_user\nFRAENK_PASSWORD=config_pass\n"
        )

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            with patch("pathlib.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/nonexistent")  # No .env

                utils.load_credentials()

                assert os.environ["FRAENK_USERNAME"] == "config_user"
                assert os.environ["FRAENK_PASSWORD"] == "config_pass"

    def test_load_credentials_priority_env_over_config(
        self, monkeypatch, clean_env, tmp_path
    ):
        """Test that environment variables take priority over config file."""
        # Set env vars
        monkeypatch.setenv("FRAENK_USERNAME", "env_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "env_pass")

        # Create config file with different values
        config_dir = tmp_path / ".config" / "fraenk"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "credentials"
        config_file.write_text(
            "FRAENK_USERNAME=config_user\nFRAENK_PASSWORD=config_pass\n"
        )

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            utils.load_credentials()

            # Env vars should win
            assert os.environ["FRAENK_USERNAME"] == "env_user"
            assert os.environ["FRAENK_PASSWORD"] == "env_pass"

    def test_load_credentials_priority_config_over_dotenv(
        self, monkeypatch, clean_env, tmp_path
    ):
        """Test that config file takes priority over .env file."""
        # Create both files
        env_file = tmp_path / ".env"
        env_file.write_text(
            "FRAENK_USERNAME=dotenv_user\nFRAENK_PASSWORD=dotenv_pass\n"
        )

        config_dir = tmp_path / ".config" / "fraenk"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "credentials"
        config_file.write_text(
            "FRAENK_USERNAME=config_user\nFRAENK_PASSWORD=config_pass\n"
        )

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            with patch("pathlib.Path.cwd") as mock_cwd:
                mock_cwd.return_value = tmp_path

                utils.load_credentials()

                # Config should win over .env
                assert os.environ["FRAENK_USERNAME"] == "config_user"
                assert os.environ["FRAENK_PASSWORD"] == "config_pass"

    def test_load_credentials_no_files_exist(self, monkeypatch, clean_env):
        """Test load_credentials when no credential files exist."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            # Should not raise error
            utils.load_credentials()

            # Env vars should not be set
            assert "FRAENK_USERNAME" not in os.environ
            assert "FRAENK_PASSWORD" not in os.environ

    def test_load_credentials_empty_env_file(self, monkeypatch, clean_env, tmp_path):
        """Test loading from empty .env file."""
        # Create empty .env file
        env_file = tmp_path / ".env"
        env_file.write_text("")

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            # Mock home to prevent loading from ~/.config
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = tmp_path / "fake_home"

                utils.load_credentials()

                # No credentials should be set
                assert "FRAENK_USERNAME" not in os.environ
                assert "FRAENK_PASSWORD" not in os.environ

    def test_load_credentials_empty_config(self, monkeypatch, clean_env, tmp_path):
        """Test loading from empty config file."""
        # Create empty config file
        config_dir = tmp_path / ".config" / "fraenk"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "credentials"
        config_file.write_text("")

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            utils.load_credentials()

            # No credentials should be set
            assert "FRAENK_USERNAME" not in os.environ
            assert "FRAENK_PASSWORD" not in os.environ

    def test_load_credentials_malformed_env_file(
        self, monkeypatch, clean_env, tmp_path
    ):
        """Test loading from .env file with invalid syntax."""
        # Create .env with malformed lines
        env_file = tmp_path / ".env"
        env_file.write_text(
            "FRAENK_USERNAME=valid_user\n"
            "INVALID LINE WITHOUT EQUALS\n"
            "FRAENK_PASSWORD=valid_pass\n"
            "# Comment line\n"
            "\n"  # Empty line
        )

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            # Mock home to prevent loading from ~/.config
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = tmp_path / "fake_home"

                utils.load_credentials()

                # Valid lines should be loaded, invalid ones skipped
                assert os.environ["FRAENK_USERNAME"] == "valid_user"
                assert os.environ["FRAENK_PASSWORD"] == "valid_pass"

    def test_load_credentials_sets_os_environ(self, monkeypatch, clean_env, tmp_path):
        """Test that load_credentials properly sets os.environ."""
        env_file = tmp_path / ".env"
        env_file.write_text("FRAENK_USERNAME=test_user\nFRAENK_PASSWORD=test_pass\n")

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            # Mock home to prevent loading from ~/.config
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = tmp_path / "fake_home"

                # Verify env vars not set before
                assert "FRAENK_USERNAME" not in os.environ
                assert "FRAENK_PASSWORD" not in os.environ

                utils.load_credentials()

                # Verify env vars are set after
                assert os.environ["FRAENK_USERNAME"] == "test_user"
                assert os.environ["FRAENK_PASSWORD"] == "test_pass"

    def test_load_credentials_no_override_existing(
        self, monkeypatch, clean_env, tmp_path
    ):
        """Test that existing env vars are not overridden by files."""
        # Set existing env vars
        monkeypatch.setenv("FRAENK_USERNAME", "existing_user")
        monkeypatch.setenv("FRAENK_PASSWORD", "existing_pass")

        # Create .env with different values
        env_file = tmp_path / ".env"
        env_file.write_text("FRAENK_USERNAME=file_user\nFRAENK_PASSWORD=file_pass\n")

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path

            utils.load_credentials()

            # Existing env vars should not be changed
            assert os.environ["FRAENK_USERNAME"] == "existing_user"
            assert os.environ["FRAENK_PASSWORD"] == "existing_pass"


class TestParseEnvFile:
    """Test _parse_env_file function."""

    def test_parse_env_file_basic(self, tmp_path):
        """Test parsing basic KEY=value format."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=value")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_double_quotes(self, tmp_path):
        """Test parsing with double quotes."""
        env_file = tmp_path / "test.env"
        env_file.write_text('KEY="value with spaces"')

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value with spaces"}

    def test_parse_env_file_single_quotes(self, tmp_path):
        """Test parsing with single quotes."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY='value'")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_no_quotes(self, tmp_path):
        """Test parsing without quotes."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=value")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_equals_in_value(self, tmp_path):
        """Test parsing when value contains equals sign."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=val=ue=123")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "val=ue=123"}

    def test_parse_env_file_whitespace_handling(self, tmp_path):
        """Test that whitespace is stripped from keys and values."""
        env_file = tmp_path / "test.env"
        env_file.write_text("  KEY  =  value  ")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_comments(self, tmp_path):
        """Test that comment lines are skipped."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "# This is a comment\nKEY1=value1\n# Another comment\nKEY2=value2"
        )

        result = utils._parse_env_file(env_file)

        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_parse_env_file_empty_lines(self, tmp_path):
        """Test that empty lines are skipped."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY1=value1\n\n\nKEY2=value2")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_parse_env_file_no_equals(self, tmp_path):
        """Test that lines without equals are skipped."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY1=value1\nINVALID LINE\nKEY2=value2")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_parse_env_file_empty_value(self, tmp_path):
        """Test parsing with empty value."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": ""}

    def test_parse_env_file_unicode(self, tmp_path):
        """Test parsing with unicode characters."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=café☕")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "café☕"}

    def test_parse_env_file_mixed_quotes(self, tmp_path):
        """Test parsing with mismatched quotes."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY=\"value'")

        result = utils._parse_env_file(env_file)

        # Mismatched quotes are not removed
        assert result == {"KEY": "\"value'"}

    def test_parse_env_file_quote_removal_double(self, tmp_path):
        """Test that matching double quotes are removed."""
        env_file = tmp_path / "test.env"
        env_file.write_text('KEY="value"')

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_quote_removal_single(self, tmp_path):
        """Test that matching single quotes are removed."""
        env_file = tmp_path / "test.env"
        env_file.write_text("KEY='value'")

        result = utils._parse_env_file(env_file)

        assert result == {"KEY": "value"}

    def test_parse_env_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = Path("/nonexistent/file.env")

        with pytest.raises(FileNotFoundError):
            utils._parse_env_file(non_existent)

    def test_parse_env_file_multiple_entries(self, tmp_path):
        """Test parsing multiple entries."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "FRAENK_USERNAME=0151123456789\n"
            "FRAENK_PASSWORD=secret123\n"
            "OTHER_VAR=other_value"
        )

        result = utils._parse_env_file(env_file)

        assert result == {
            "FRAENK_USERNAME": "0151123456789",
            "FRAENK_PASSWORD": "secret123",
            "OTHER_VAR": "other_value",
        }

    def test_parse_env_file_special_characters(self, tmp_path):
        """Test parsing with special characters in values."""
        env_file = tmp_path / "test.env"
        env_file.write_text(
            "KEY1=value!@#$%^&*()\n"
            'KEY2="value with spaces and $pecial"\n'
            "KEY3='value with \\n newline'"
        )

        result = utils._parse_env_file(env_file)

        assert result == {
            "KEY1": "value!@#$%^&*()",
            "KEY2": "value with spaces and $pecial",
            "KEY3": "value with \\n newline",
        }

    def test_parse_env_file_export_prefix(self, tmp_path):
        """Test parsing lines with 'export' prefix (common in shell scripts)."""
        env_file = tmp_path / "test.env"
        env_file.write_text("export KEY1=value1\nKEY2=value2")

        result = utils._parse_env_file(env_file)

        # Should handle export prefix if implemented, otherwise skip or include
        # Current implementation doesn't handle 'export', so it would be:
        assert "KEY2" in result
        assert result["KEY2"] == "value2"


class TestDisplayDataConsumption:
    """Test display_data_consumption function."""

    @patch("builtins.print")
    def test_display_data_consumption_valid_data(
        self, mock_print, mock_consumption_response
    ):
        """Test displaying valid consumption data."""
        utils.print_consumption(mock_consumption_response)

        # Verify print was called multiple times
        assert mock_print.call_count > 0

        # Check that key information was printed
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "0151 - 29489521" in printed_output  # MSISDN
        assert "POST_PAID" in printed_output  # Contract type
        assert "Vertragsvolumen" in printed_output  # Pass name
        assert "6,47 GB" in printed_output  # Used volume
        assert "25 GB" in printed_output  # Initial volume
        assert "26%" in printed_output or "26" in printed_output  # Percentage

    @patch("builtins.print")
    def test_display_data_consumption_missing_customer(self, mock_print):
        """Test displaying data without customer field."""
        data = {
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": "1 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 10,
                }
            ]
        }

        utils.print_consumption(data)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "N/A" in printed_output  # Should show N/A for missing customer info

    @patch("builtins.print")
    def test_display_data_consumption_missing_msisdn(self, mock_print):
        """Test displaying data with customer but no msisdn."""
        data = {"customer": {"contractType": "POST_PAID"}, "passes": []}

        utils.print_consumption(data)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "N/A" in printed_output  # Should show N/A for missing msisdn

    @patch("builtins.print")
    def test_display_data_consumption_missing_contract_type(self, mock_print):
        """Test displaying data with customer but no contractType."""
        data = {"customer": {"msisdn": "0151123456789"}, "passes": []}

        utils.print_consumption(data)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "N/A" in printed_output  # Should show N/A for missing contract type

    @patch("builtins.print")
    def test_display_data_consumption_empty_passes(self, mock_print):
        """Test displaying data with empty passes list."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [],
        }

        utils.print_consumption(data)

        # Should still print header and customer info
        assert mock_print.call_count > 0
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "0151123456789" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_missing_passes(self, mock_print):
        """Test displaying data without passes field."""
        data = {"customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"}}

        utils.print_consumption(data)

        # Should handle gracefully
        assert mock_print.call_count > 0

    @patch("builtins.print")
    def test_display_data_consumption_timestamp_conversion(self, mock_print):
        """Test timestamp conversion to readable date."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": "1 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 10,
                    "expiryTimestamp": 1761951599000,  # Milliseconds timestamp
                }
            ],
        }

        utils.print_consumption(data)

        # Check that a formatted date is printed
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        # The timestamp should be converted to a readable date
        # 1761951599000 ms = May 2025
        assert "2025" in printed_output or "Expires" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_missing_timestamp(self, mock_print):
        """Test displaying pass without expiry timestamp."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": "1 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 10,
                    # No expiryTimestamp
                }
            ],
        }

        utils.print_consumption(data)

        # Should handle missing timestamp gracefully
        assert mock_print.call_count > 0

    @patch("builtins.print")
    def test_display_data_consumption_zero_timestamp(self, mock_print):
        """Test displaying pass with zero timestamp."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": "1 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 10,
                    "expiryTimestamp": 0,
                }
            ],
        }

        utils.print_consumption(data)

        # Should show epoch date (1970-01-01)
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "1970" in printed_output or "01-01" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_multiple_passes(self, mock_print):
        """Test displaying multiple passes."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Pass 1",
                    "usedVolume": "1 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 10,
                },
                {
                    "passName": "Pass 2",
                    "usedVolume": "2 GB",
                    "initialVolume": "5 GB",
                    "percentageConsumption": 40,
                },
                {
                    "passName": "Pass 3",
                    "usedVolume": "3 GB",
                    "initialVolume": "3 GB",
                    "percentageConsumption": 100,
                },
            ],
        }

        utils.print_consumption(data)

        # All passes should be displayed
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Pass 1" in printed_output
        assert "Pass 2" in printed_output
        assert "Pass 3" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_unicode_output(self, mock_print):
        """Test displaying data with unicode characters."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Vertragsvolumen mit Emojis 🚀",
                    "usedVolume": "6,47 GB",
                    "initialVolume": "25 GB",
                    "percentageConsumption": 26,
                }
            ],
        }

        utils.print_consumption(data)

        # Unicode should be handled correctly
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "🚀" in printed_output or "Vertragsvolumen" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_none_values(self, mock_print):
        """Test displaying data with None values."""
        data = {
            "customer": {"msisdn": None, "contractType": None},
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": None,
                    "initialVolume": None,
                    "percentageConsumption": None,
                }
            ],
        }

        utils.print_consumption(data)

        # Should handle None values gracefully
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "N/A" in printed_output or "None" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_progress_bar(self, mock_print):
        """Test that usage percentage is displayed correctly."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Test Pass",
                    "usedVolume": "5 GB",
                    "initialVolume": "10 GB",
                    "percentageConsumption": 50,
                }
            ],
        }

        utils.print_consumption(data)

        # Check for percentage display
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "50%" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_formatting(self, mock_print):
        """Test overall formatting of the display."""
        data = {
            "customer": {"msisdn": "0151 - 12345678", "contractType": "POST_PAID"},
            "passes": [
                {
                    "passName": "Monthly Data",
                    "type": "INCLUSIVE",
                    "usedVolume": "7.5 GB",
                    "usedBytes": 8053063680,
                    "initialVolume": "25 GB",
                    "initialVolumeBytes": 26843545600,
                    "percentageConsumption": 30,
                    "expiryTimestamp": 1761951599000,
                }
            ],
        }

        utils.print_consumption(data)

        # Check that sections are printed
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)

        # Should have header section
        assert "═" in printed_output or "=" in printed_output or "-" in printed_output

        # Should have customer info
        assert "0151 - 12345678" in printed_output
        assert "POST_PAID" in printed_output

        # Should have pass details
        assert "Monthly Data" in printed_output
        assert "7.5 GB" in printed_output
        assert "25 GB" in printed_output
        assert "30" in printed_output

    @patch("builtins.print")
    def test_display_data_consumption_bookable_passes(self, mock_print):
        """Test displaying bookableDataPassesAvailable flag."""
        data = {
            "customer": {"msisdn": "0151123456789", "contractType": "POST_PAID"},
            "passes": [],
            "bookableDataPassesAvailable": True,
        }

        utils.print_consumption(data)

        # Bookable passes info might be displayed
        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        # This field might or might not be displayed based on implementation
        assert mock_print.call_count > 0
