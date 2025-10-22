"""Comprehensive unit tests for the FraenkAPI client class."""

import base64
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest
import requests
import responses

from fraenk_api.client import FraenkAPI


class TestFraenkAPIInitialization:
    """Test FraenkAPI class initialization."""

    def test_init_creates_instance_with_none_values(self):
        """Test that new FraenkAPI instance has all attributes set to None."""
        client = FraenkAPI()

        assert client.access_token is None
        assert client.refresh_token is None
        assert client.customer_id is None
        assert client.contract_id is None

    def test_init_sets_base_url(self):
        """Test that BASE_URL class attribute is correctly set."""
        client = FraenkAPI()

        assert client.BASE_URL == "https://app.fraenk.de/fraenk-rest-service/app/v13"


class TestBaseHeaders:
    """Test _base_headers method."""

    def test_base_headers_returns_correct_structure(self, mock_api_headers):
        """Test that _base_headers returns all required Android app headers."""
        client = FraenkAPI()
        headers = client._base_headers()

        assert headers == mock_api_headers

    def test_base_headers_contains_required_tenant(self):
        """Test that X-Tenant header is set to fraenk."""
        client = FraenkAPI()
        headers = client._base_headers()

        assert headers["X-Tenant"] == "fraenk"

    def test_base_headers_mimics_android_app(self):
        """Test that headers mimic Android app for API compatibility."""
        client = FraenkAPI()
        headers = client._base_headers()

        assert headers["X-App-OS"] == "Android"
        assert headers["X-App-Device"] == "Python-Client"
        assert headers["X-App-Device-Vendor"] == "Python"
        assert headers["X-App-OS-Version"] == "13"
        assert headers["X-App-Version"] == "1.13.9"

    def test_base_headers_no_authorization(self):
        """Test that _base_headers does not include Authorization header."""
        client = FraenkAPI()
        headers = client._base_headers()

        assert "Authorization" not in headers


class TestAuthHeaders:
    """Test _auth_headers method."""

    def test_auth_headers_without_token(self, mock_api_headers):
        """Test that _auth_headers returns base headers when no token is set."""
        client = FraenkAPI()
        headers = client._auth_headers()

        assert headers == mock_api_headers
        assert "Authorization" not in headers

    def test_auth_headers_with_access_token(self, mock_api_headers):
        """Test that _auth_headers includes Bearer token when access_token is set."""
        client = FraenkAPI()
        client.access_token = "test-token-abc123"
        headers = client._auth_headers()

        expected_headers = {**mock_api_headers, "Authorization": "Bearer test-token-abc123"}
        assert headers == expected_headers

    def test_auth_headers_bearer_format(self):
        """Test that Authorization header uses correct Bearer token format."""
        client = FraenkAPI()
        client.access_token = "my-jwt-token"
        headers = client._auth_headers()

        assert headers["Authorization"] == "Bearer my-jwt-token"

    def test_auth_headers_includes_base_headers(self):
        """Test that _auth_headers includes all base headers."""
        client = FraenkAPI()
        client.access_token = "token"
        headers = client._auth_headers()

        assert "X-Tenant" in headers
        assert "X-App-OS" in headers
        assert "X-App-Device" in headers


class TestLoginInitiate:
    """Test login_initiate method (MFA step 1)."""

    @responses.activate
    def test_login_initiate_mfa_required_success(self, mock_mfa_response):
        """Test successful login_initiate returns MFA response on 401."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json=mock_mfa_response,
            status=401
        )

        result = client.login_initiate("0151123456789", "password123")

        assert result == mock_mfa_response
        assert result["error"] == "mfa_required"
        assert "mfa_token" in result

    @responses.activate
    def test_login_initiate_sends_correct_request_data(self):
        """Test that login_initiate sends correct form data."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json={"error": "mfa_required", "mfa_token": "token"},
            status=401
        )

        client.login_initiate("testuser", "testpass")

        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "grant_type=password" in request.body
        assert "username=testuser" in request.body
        assert "password=testpass" in request.body
        assert "scope=app" in request.body

    @responses.activate
    def test_login_initiate_sends_correct_headers(self, mock_api_headers):
        """Test that login_initiate includes base headers and Content-Type."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json={"error": "mfa_required", "mfa_token": "token"},
            status=401
        )

        client.login_initiate("user", "pass")

        request = responses.calls[0].request
        assert request.headers["X-Tenant"] == "fraenk"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"

    @responses.activate
    def test_login_initiate_200_success_without_mfa(self):
        """Test login_initiate handles 200 response (no MFA required)."""
        client = FraenkAPI()

        auth_response = {"access_token": "token", "refresh_token": "refresh"}
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json=auth_response,
            status=200
        )

        result = client.login_initiate("user", "pass")

        assert result == auth_response

    @responses.activate
    def test_login_initiate_401_without_mfa_error_raises(self):
        """Test that 401 without mfa_required error raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json={"error": "invalid_credentials"},
            status=401
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_initiate("user", "wrongpass")

    @responses.activate
    def test_login_initiate_500_error_raises(self):
        """Test that server error (500) raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json={"error": "server_error"},
            status=500
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_initiate("user", "pass")

    @responses.activate
    def test_login_initiate_403_forbidden_raises(self):
        """Test that 403 Forbidden raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json={"error": "forbidden"},
            status=403
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_initiate("user", "pass")

    @responses.activate
    def test_login_initiate_network_error_raises(self):
        """Test that network errors are propagated."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            body=requests.exceptions.ConnectionError("Network unreachable")
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            client.login_initiate("user", "pass")

    @responses.activate
    def test_login_initiate_timeout_raises(self):
        """Test that timeout errors are propagated."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            body=requests.exceptions.Timeout("Request timeout")
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.login_initiate("user", "pass")

    @responses.activate
    def test_login_initiate_malformed_json_raises(self):
        """Test that malformed JSON response raises JSONDecodeError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            body="not valid json",
            status=401
        )

        with pytest.raises(requests.exceptions.JSONDecodeError):
            client.login_initiate("user", "pass")


class TestLoginComplete:
    """Test login_complete method (MFA step 2)."""

    @responses.activate
    def test_login_complete_success_sets_tokens(self, mock_login_response):
        """Test successful login_complete sets access and refresh tokens."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json=mock_login_response,
            status=200
        )

        result = client.login_complete("user", "pass", "123456", "mfa-token")

        assert client.access_token == mock_login_response["access_token"]
        assert client.refresh_token == mock_login_response["refresh_token"]
        assert result == mock_login_response

    @responses.activate
    def test_login_complete_extracts_customer_id_from_jwt(self, mock_login_response):
        """Test that login_complete extracts customer ID from JWT sub field."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json=mock_login_response,
            status=200
        )

        client.login_complete("user", "pass", "123456", "mfa-token")

        assert client.customer_id == "7555659511"

    @responses.activate
    def test_login_complete_sends_correct_request_data(self):
        """Test that login_complete sends all required MFA parameters."""
        client = FraenkAPI()

        jwt = _create_jwt_token("f:uuid:12345")
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": jwt, "refresh_token": "refresh"},
            status=200
        )

        client.login_complete("testuser", "testpass", "654321", "test-mfa-token")

        request = responses.calls[0].request
        assert "username=testuser" in request.body
        assert "password=testpass" in request.body
        assert "mtan=654321" in request.body
        assert "mfa_token=test-mfa-token" in request.body

    @responses.activate
    def test_login_complete_sends_correct_headers(self):
        """Test that login_complete includes base headers and Content-Type."""
        client = FraenkAPI()

        jwt = _create_jwt_token("f:uuid:12345")
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": jwt, "refresh_token": "refresh"},
            status=200
        )

        client.login_complete("user", "pass", "123456", "mfa-token")

        request = responses.calls[0].request
        assert request.headers["X-Tenant"] == "fraenk"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"

    @responses.activate
    def test_login_complete_jwt_parsing_with_colon_format(self):
        """Test JWT parsing with colon-separated format (f:uuid:ID)."""
        client = FraenkAPI()

        jwt = _create_jwt_token("f:uuid:9876543210")
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": jwt, "refresh_token": "refresh"},
            status=200
        )

        client.login_complete("user", "pass", "123456", "mfa-token")

        assert client.customer_id == "9876543210"

    @responses.activate
    def test_login_complete_jwt_parsing_without_colon(self):
        """Test JWT parsing when sub field has no colons (direct ID)."""
        client = FraenkAPI()

        jwt = _create_jwt_token("direct-customer-id-123")
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": jwt, "refresh_token": "refresh"},
            status=200
        )

        client.login_complete("user", "pass", "123456", "mfa-token")

        assert client.customer_id == "direct-customer-id-123"

    @responses.activate
    def test_login_complete_jwt_parsing_handles_padding(self):
        """Test JWT parsing correctly handles base64 padding."""
        client = FraenkAPI()

        # Create JWT with payload that needs padding
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {"sub": "f:uuid:111", "iat": 1234567890}

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        jwt = f"{header_b64}.{payload_b64}.signature"

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": jwt, "refresh_token": "refresh"},
            status=200
        )

        client.login_complete("user", "pass", "123456", "mfa-token")

        assert client.customer_id == "111"

    @responses.activate
    def test_login_complete_401_error_raises(self):
        """Test that 401 error (invalid MFA code) raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"error": "invalid_mfa_code"},
            status=401
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_complete("user", "pass", "wrong-code", "mfa-token")

    @responses.activate
    def test_login_complete_403_error_raises(self):
        """Test that 403 error raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"error": "forbidden"},
            status=403
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_complete("user", "pass", "123456", "mfa-token")

    @responses.activate
    def test_login_complete_500_error_raises(self):
        """Test that server error raises HTTPError."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"error": "server_error"},
            status=500
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.login_complete("user", "pass", "123456", "mfa-token")

    @responses.activate
    def test_login_complete_malformed_jwt_raises(self):
        """Test that malformed JWT (not enough parts) raises IndexError."""
        client = FraenkAPI()

        # JWT with only one part (missing payload)
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": "only-one-part", "refresh_token": "refresh"},
            status=200
        )

        with pytest.raises(IndexError):
            client.login_complete("user", "pass", "123456", "mfa-token")

    @responses.activate
    def test_login_complete_invalid_base64_raises(self):
        """Test that invalid base64 in JWT raises base64 decode error."""
        client = FraenkAPI()

        # Invalid base64 characters
        invalid_jwt = "header.!!!invalid-base64!!!.signature"
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": invalid_jwt, "refresh_token": "refresh"},
            status=200
        )

        with pytest.raises(Exception):  # base64 decode error
            client.login_complete("user", "pass", "123456", "mfa-token")

    @responses.activate
    def test_login_complete_invalid_json_in_jwt_raises(self):
        """Test that invalid JSON in JWT payload raises JSONDecodeError."""
        client = FraenkAPI()

        # Valid base64 but invalid JSON content
        invalid_jwt = "header.bm90LXZhbGlkLWpzb24.signature"
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json={"access_token": invalid_jwt, "refresh_token": "refresh"},
            status=200
        )

        with pytest.raises(json.JSONDecodeError):
            client.login_complete("user", "pass", "123456", "mfa-token")

    @responses.activate
    def test_login_complete_network_error_raises(self):
        """Test that network errors are propagated."""
        client = FraenkAPI()

        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            body=requests.exceptions.ConnectionError("Network unreachable")
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            client.login_complete("user", "pass", "123456", "mfa-token")


class TestGetContracts:
    """Test get_contracts method."""

    @responses.activate
    def test_get_contracts_success_returns_list(self, mock_contracts_response):
        """Test successful get_contracts returns contract list."""
        client = FraenkAPI()
        client.access_token = "valid-token"
        client.customer_id = "7555659511"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts",
            json=mock_contracts_response,
            status=200
        )

        result = client.get_contracts()

        assert result == mock_contracts_response
        assert len(result) == 2

    @responses.activate
    def test_get_contracts_sets_contract_id_from_first_contract(self, mock_contracts_response):
        """Test that get_contracts sets contract_id to first contract's ID."""
        client = FraenkAPI()
        client.access_token = "valid-token"
        client.customer_id = "7555659511"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts",
            json=mock_contracts_response,
            status=200
        )

        client.get_contracts()

        assert client.contract_id == "12345678"

    @responses.activate
    def test_get_contracts_empty_list_does_not_set_contract_id(self):
        """Test that empty contracts list doesn't set contract_id."""
        client = FraenkAPI()
        client.access_token = "valid-token"
        client.customer_id = "7555659511"
        client.contract_id = "previous-id"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts",
            json=[],
            status=200
        )

        result = client.get_contracts()

        assert result == []
        assert client.contract_id == "previous-id"

    @responses.activate
    def test_get_contracts_sends_auth_headers(self):
        """Test that get_contracts includes Authorization header."""
        client = FraenkAPI()
        client.access_token = "my-access-token"
        client.customer_id = "12345"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts",
            json=[],
            status=200
        )

        client.get_contracts()

        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer my-access-token"
        assert request.headers["X-Tenant"] == "fraenk"

    @responses.activate
    def test_get_contracts_uses_customer_id_in_url(self):
        """Test that get_contracts uses correct customer ID in URL."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "9999999999"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/9999999999/contracts",
            json=[],
            status=200
        )

        client.get_contracts()

        assert len(responses.calls) == 1
        assert "9999999999" in responses.calls[0].request.url

    @responses.activate
    def test_get_contracts_401_unauthorized_raises(self):
        """Test that 401 unauthorized raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "invalid-token"
        client.customer_id = "12345"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts",
            json={"error": "unauthorized"},
            status=401
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_contracts()

    @responses.activate
    def test_get_contracts_403_forbidden_raises(self):
        """Test that 403 forbidden raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts",
            json={"error": "forbidden"},
            status=403
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_contracts()

    @responses.activate
    def test_get_contracts_404_not_found_raises(self):
        """Test that 404 not found raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "nonexistent"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/nonexistent/contracts",
            json={"error": "not_found"},
            status=404
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_contracts()

    @responses.activate
    def test_get_contracts_500_server_error_raises(self):
        """Test that 500 server error raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts",
            json={"error": "server_error"},
            status=500
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_contracts()

    @responses.activate
    def test_get_contracts_network_error_raises(self):
        """Test that network errors are propagated."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts",
            body=requests.exceptions.ConnectionError("Network error")
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            client.get_contracts()


class TestGetDataConsumption:
    """Test get_data_consumption method."""

    @responses.activate
    def test_get_data_consumption_success_returns_dict(self, mock_consumption_response):
        """Test successful get_data_consumption returns consumption data."""
        client = FraenkAPI()
        client.access_token = "valid-token"
        client.customer_id = "7555659511"
        client.contract_id = "12345678"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts/12345678/dataconsumption",
            json=mock_consumption_response,
            status=200
        )

        result = client.get_data_consumption()

        assert result == mock_consumption_response
        assert "customer" in result
        assert "passes" in result

    @responses.activate
    def test_get_data_consumption_without_cache_sends_no_cache_header(self):
        """Test that use_cache=False includes Cache-Control: no-cache header."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={},
            status=200
        )

        client.get_data_consumption(use_cache=False)

        request = responses.calls[0].request
        assert request.headers["Cache-Control"] == "no-cache"

    @responses.activate
    def test_get_data_consumption_with_cache_no_cache_control_header(self):
        """Test that use_cache=True does not include Cache-Control header."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={},
            status=200
        )

        client.get_data_consumption(use_cache=True)

        request = responses.calls[0].request
        assert "Cache-Control" not in request.headers

    @responses.activate
    def test_get_data_consumption_default_is_no_cache(self):
        """Test that default behavior (no use_cache param) sends no-cache."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={},
            status=200
        )

        client.get_data_consumption()

        request = responses.calls[0].request
        assert request.headers["Cache-Control"] == "no-cache"

    @responses.activate
    def test_get_data_consumption_sends_auth_headers(self):
        """Test that get_data_consumption includes Authorization header."""
        client = FraenkAPI()
        client.access_token = "my-token-xyz"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={},
            status=200
        )

        client.get_data_consumption()

        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer my-token-xyz"
        assert request.headers["X-Tenant"] == "fraenk"

    @responses.activate
    def test_get_data_consumption_uses_customer_and_contract_ids(self):
        """Test that get_data_consumption uses correct IDs in URL."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "1111111111"
        client.contract_id = "2222222222"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/1111111111/contracts/2222222222/dataconsumption",
            json={},
            status=200
        )

        client.get_data_consumption()

        url = responses.calls[0].request.url
        assert "1111111111" in url
        assert "2222222222" in url

    @responses.activate
    def test_get_data_consumption_401_unauthorized_raises(self):
        """Test that 401 unauthorized raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "expired-token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={"error": "unauthorized"},
            status=401
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_data_consumption()

    @responses.activate
    def test_get_data_consumption_403_forbidden_raises(self):
        """Test that 403 forbidden raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={"error": "forbidden"},
            status=403
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_data_consumption()

    @responses.activate
    def test_get_data_consumption_404_not_found_raises(self):
        """Test that 404 not found raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "nonexistent"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/nonexistent/dataconsumption",
            json={"error": "not_found"},
            status=404
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_data_consumption()

    @responses.activate
    def test_get_data_consumption_500_server_error_raises(self):
        """Test that 500 server error raises HTTPError."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            json={"error": "server_error"},
            status=500
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_data_consumption()

    @responses.activate
    def test_get_data_consumption_network_error_raises(self):
        """Test that network errors are propagated."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            body=requests.exceptions.ConnectionError("Network error")
        )

        with pytest.raises(requests.exceptions.ConnectionError):
            client.get_data_consumption()

    @responses.activate
    def test_get_data_consumption_timeout_raises(self):
        """Test that timeout errors are propagated."""
        client = FraenkAPI()
        client.access_token = "token"
        client.customer_id = "12345"
        client.contract_id = "67890"

        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/12345/contracts/67890/dataconsumption",
            body=requests.exceptions.Timeout("Request timeout")
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.get_data_consumption()


class TestIntegrationScenarios:
    """Test full authentication and data retrieval flows."""

    @responses.activate
    def test_full_mfa_login_flow(self, mock_mfa_response, mock_login_response):
        """Test complete MFA login flow from initiate to complete."""
        client = FraenkAPI()

        # Step 1: Initiate login
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login",
            json=mock_mfa_response,
            status=401
        )

        mfa_response = client.login_initiate("user", "pass")
        assert mfa_response["error"] == "mfa_required"

        # Step 2: Complete login
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json=mock_login_response,
            status=200
        )

        auth = client.login_complete("user", "pass", "123456", mfa_response["mfa_token"])

        assert client.access_token is not None
        assert client.refresh_token is not None
        assert client.customer_id == "7555659511"

    @responses.activate
    def test_full_data_retrieval_flow(self, mock_login_response, mock_contracts_response, mock_consumption_response):
        """Test complete flow from login to data consumption retrieval."""
        client = FraenkAPI()

        # Login
        responses.add(
            responses.POST,
            f"{client.BASE_URL}/login-with-mfa",
            json=mock_login_response,
            status=200
        )
        client.login_complete("user", "pass", "123456", "mfa-token")

        # Get contracts
        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts",
            json=mock_contracts_response,
            status=200
        )
        contracts = client.get_contracts()
        assert len(contracts) == 2
        assert client.contract_id == "12345678"

        # Get consumption
        responses.add(
            responses.GET,
            f"{client.BASE_URL}/customers/7555659511/contracts/12345678/dataconsumption",
            json=mock_consumption_response,
            status=200
        )
        consumption = client.get_data_consumption()
        assert "passes" in consumption
        assert consumption["customer"]["msisdn"] == "0151 - 29489521"


# Helper functions

def _create_jwt_token(sub_value: str) -> str:
    """Create a valid JWT token with specified sub field value.

    Args:
        sub_value: Value for the sub field in JWT payload

    Returns:
        Valid JWT token string in format header.payload.signature
    """
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "sub": sub_value,
        "iat": 1234567890,
        "exp": 1234567890,
        "iss": "fraenk"
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "fake-signature"

    return f"{header_b64}.{payload_b64}.{signature}"
