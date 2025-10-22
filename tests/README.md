# Fraenk API Test Suite

Comprehensive test suite for the Fraenk API Python client, achieving **98.95% code coverage** across all modules.

## Test Statistics

- **Total Tests**: 174
- **Overall Coverage**: 98.95%
- **Test Files**: 6
- **Lines Covered**: 188/190

### Coverage by Module

| Module | Lines | Coverage | Missing |
|--------|-------|----------|---------|
| `src/fraenk_api/__init__.py` | 3 | 100% | None |
| `src/fraenk_api/__main__.py` | 3 | 66.67% | Line 6 |
| `src/fraenk_api/cli.py` | 78 | 98.72% | Line 134 |
| `src/fraenk_api/client.py` | 63 | 100% | None |
| `src/fraenk_api/utils.py` | 43 | 100% | None |

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run specific test file
```bash
uv run pytest tests/test_client.py
```

### Run tests with coverage
```bash
uv run pytest --cov=src/fraenk_api --cov-report=term-missing
```

### Run tests with HTML coverage report
```bash
uv run pytest --cov=src/fraenk_api --cov-report=html
# Open htmlcov/index.html in your browser
```

### Run specific test class
```bash
uv run pytest tests/test_client.py::TestLoginComplete
```

### Run specific test
```bash
uv run pytest tests/test_client.py::TestLoginComplete::test_login_complete_success

## Test Structure

### `test_client.py` (58 tests)
Comprehensive tests for the `FraenkAPI` class:

- **TestFraenkAPIInitialization** (2 tests) - Instance creation and defaults
- **TestBaseHeaders** (4 tests) - HTTP header generation
- **TestAuthHeaders** (4 tests) - Authorization header handling
- **TestLoginInitiate** (10 tests) - MFA login initiation
- **TestLoginComplete** (14 tests) - Login completion with JWT parsing
- **TestGetContracts** (10 tests) - Contract fetching
- **TestGetDataConsumption** (12 tests) - Data consumption retrieval
- **TestIntegrationScenarios** (2 tests) - End-to-end flows

### `test_cli.py` (66 tests)
Tests for the CLI module:

- **TestLoadFixture** (5 tests) - Fixture loading for dry-run mode
- **TestArgumentParsing** (10 tests) - Command-line argument parsing
- **TestDryRunMode** (8 tests) - Dry-run mode with fixtures
- **TestCredentialLoading** (5 tests) - Credential loading chain
- **TestLoginFlow** (10 tests) - MFA login flow via CLI
- **TestDataFetching** (8 tests) - Data fetching operations
- **TestOutputModes** (5 tests) - JSON vs pretty output
- **TestErrorHandling** (6 tests) - Error handling and messages
- **TestIntegrationScenarios** (4 tests) - Complete CLI flows
- **TestEdgeCases** (5 tests) - Edge cases and boundaries

### `test_utils.py` (46 tests)
Tests for utility functions:

- **TestLoadCredentials** (11 tests) - Credential loading from multiple sources
- **TestParseEnvFile** (20 tests) - ENV file parsing with various formats
- **TestDisplayDataConsumption** (15 tests) - Data display formatting

### `test_init.py` (4 tests)
Package initialization tests:
- Package exports
- Version string
- `__all__` list
- Class accessibility

### `test_main.py` (2 tests)
Entry point tests:
- Module execution
- Import behavior

### `conftest.py`
Shared pytest fixtures:

- `mock_mfa_response` - Standard MFA response
- `mock_jwt_token` - Valid JWT with customer ID
- `mock_login_response` - Successful login response
- `mock_contracts_response` - Mock contracts data
- `mock_consumption_response` - Mock consumption data
- `mock_api_headers` - Expected API headers
- `temp_env_file` - Temporary .env file for testing
- `temp_config_file` - Temporary config file for testing
- `fixture_contracts` - Actual contracts fixture data
- `fixture_consumption` - Actual consumption fixture data
- `clean_env` - Environment variable cleanup
- `mock_stdin` - Mock stdin for SMS input

## Test Categories

### Unit Tests
- Class initialization
- Header generation
- JWT parsing
- API request/response handling
- Error handling

### Edge Cases
- Malformed JWT tokens
- Invalid base64 encoding
- Network errors and timeouts
- Various HTTP error codes (401, 403, 404, 500)
- Empty responses
- Cache control behavior

### Integration Tests
- Full MFA login flow (initiate → complete)
- Complete data retrieval flow (login → contracts → consumption)

## Mocking Strategy

All HTTP requests are mocked using the `responses` library:
- No actual API calls made during tests
- Predictable, fast test execution
- Tests can run offline
- No SMS codes required

## Adding New Tests

1. Add test fixtures to `conftest.py` if needed
2. Create test class in appropriate test file
3. Use `@responses.activate` decorator for HTTP mocking
4. Follow naming convention: `test_<method>_<scenario>_<expected_result>`
5. Include docstrings explaining what is being tested
6. Verify coverage with `pytest --cov`

## Dependencies

Test dependencies are in `pyproject.toml` under `[project.optional-dependencies]`:
- `pytest>=8.3.0`: Test framework
- `pytest-cov>=5.0.0`: Coverage reporting
- `responses>=0.25.0`: HTTP request mocking

Install with:
```bash
uv pip install -e ".[dev]"
```
