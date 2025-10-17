"""Fraenk API client for mobile data consumption tracking.

Unofficial Python client for tracking mobile data consumption from Fraenk
mobile service via reverse-engineered API.

Example:
    >>> from fraenk_api import FraenkAPI
    >>> api = FraenkAPI()
    >>> mfa_response = api.login_initiate("email@example.com", "password")
    >>> mfa_token = mfa_response["mfa_token"]
    >>> sms_code = input("Enter SMS code: ")
    >>> api.login_complete("email@example.com", "password", sms_code, mfa_token)
    >>> api.get_contracts()
    >>> data = api.get_data_consumption()
"""

from fraenk_api.client import FraenkAPI

__version__ = "0.1.0"
__all__ = ["FraenkAPI"]
