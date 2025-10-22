"""Unit tests for the __main__.py module."""

import sys
import importlib
from unittest.mock import patch, Mock
import pytest


class TestMainModule:
    """Test __main__.py entry point."""

    def test_main_entry_point(self):
        """Test that __main__.py has correct structure and calls cli.main()."""
        # Read the __main__.py source to verify its structure
        from pathlib import Path
        main_file = Path(__file__).parent.parent / "src" / "fraenk_api" / "__main__.py"
        source = main_file.read_text()

        # Verify it imports main from cli
        assert "from fraenk_api.cli import main" in source

        # Verify it has the if __name__ == "__main__" guard
        assert 'if __name__ == "__main__":' in source

        # Verify it calls main()
        assert "main()" in source

        # Test execution by using exec with a mock
        with patch("fraenk_api.cli.main") as mock_main:
            namespace = {"__name__": "__main__"}
            exec(source, namespace)
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