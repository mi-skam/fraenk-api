"""Unit tests for the __init__.py module."""

import pytest
from fraenk_api import FraenkAPI, __version__, __all__


class TestPackageExports:
    """Test package exports and metadata."""

    def test_package_exports_fraenk_api(self):
        """Test that FraenkAPI can be imported from package."""
        # This tests the import
        assert FraenkAPI is not None
        assert callable(FraenkAPI)

    def test_package_version(self):
        """Test that __version__ is set correctly."""
        assert __version__ == "0.1.0"
        assert isinstance(__version__, str)

    def test_package_all(self):
        """Test that __all__ contains expected exports."""
        assert __all__ == ["FraenkAPI"]
        assert isinstance(__all__, list)

    def test_fraenk_api_class_accessible(self):
        """Test that FraenkAPI class can be instantiated."""
        api = FraenkAPI()
        assert api is not None
        assert hasattr(api, "login_initiate")
        assert hasattr(api, "login_complete")
        assert hasattr(api, "get_contracts")
        assert hasattr(api, "get_data_consumption")