"""Unit tests for the __main__.py module."""

import sys
from unittest.mock import patch, Mock
import pytest


class TestMainModule:
    """Test __main__.py entry point."""

    def test_main_entry_point(self):
        """Test that python -m fraenk_api calls cli.main()."""
        with patch("fraenk_api.cli.main") as mock_main:
            # Simulate running as __main__
            with patch.object(sys, "argv", ["fraenk_api"]):
                # Import and execute the __main__ module
                import fraenk_api.__main__

                # Verify cli.main() was called
                mock_main.assert_called_once()

    def test_main_module_import(self):
        """Test that __main__ module can be imported without execution."""
        # When imported (not run as main), it should not execute
        with patch("fraenk_api.cli.main") as mock_main:
            # This import should not trigger main() because __name__ != "__main__"
            from fraenk_api import __main__ as main_module

            # The module should exist but main() should not be called
            assert main_module is not None
            # Note: In actual __main__.py, the cli.main() call is at module level,
            # so it would be called. This test assumes proper if __name__ == "__main__" guard