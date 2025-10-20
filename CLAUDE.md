# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Python client for tracking mobile data consumption from Fraenk mobile service via reverse-engineered API. Uses MFA (SMS-based) authentication and requires user interaction for SMS codes.

## Development Commands

### Running the CLI
```bash
# Standard usage (requires SMS for MFA)
uv run fraenk

# JSON output to stdout
uv run fraenk -j

# Dry-run mode (uses fixtures, no API calls, no SMS required)
uv run fraenk -d

# Quiet mode (suppress progress messages)
uv run fraenk -q

# Alternative: run as module
uv run python -m fraenk_api
```

### Setup

**Credentials Configuration (Fallback Chain)**

The CLI loads credentials from multiple sources with the following priority:
1. **Environment variables** (highest priority) - Best for CI/automation
2. **Config file at `~/.config/fraenk/credentials`** - Best for installed usage
3. **.env in current directory** (lowest priority) - Best for development

All sources use the same KEY=VALUE format:
```bash
FRAENK_USERNAME=your_phone_number
FRAENK_PASSWORD=your_password
```

**Development setup:**
```bash
# Configure credentials in .env
cp .env.example .env
# Then edit .env with FRAENK_USERNAME and FRAENK_PASSWORD
```

**Installed usage:**
```bash
# Create config directory and file
mkdir -p ~/.config/fraenk
echo "FRAENK_USERNAME=your_phone_number" > ~/.config/fraenk/credentials
echo "FRAENK_PASSWORD=your_password" >> ~/.config/fraenk/credentials
chmod 600 ~/.config/fraenk/credentials  # Recommended for security
```

**CI/Automation:**
```bash
# Set environment variables directly
export FRAENK_USERNAME=your_phone_number
export FRAENK_PASSWORD=your_password
```

Dependencies are managed via pyproject.toml. No manual installation needed with uv.

## Architecture

### Package Structure (src layout)
- **src/fraenk_api/client.py**: Core `FraenkAPI` class with authentication and data fetching
- **src/fraenk_api/cli.py**: CLI implementation with argparse (includes dry-run fixture support)
- **src/fraenk_api/utils.py**: Helper functions (display formatting, .env loading)
- **src/fraenk_api/__init__.py**: Package exports
- **src/fraenk_api/__main__.py**: Entry point for `python -m fraenk_api`

### Console Script
Entry point defined in pyproject.toml: `fraenk = "fraenk_api.cli:main"`

### Key Implementation Patterns

**MFA Authentication (Two-Step)**
1. `login_initiate()` - Returns mfa_token, SMS sent to phone (HTTP 401 with `mfa_required` is expected)
2. `login_complete()` - Accepts SMS code, returns access_token and refresh_token

**JWT Customer ID Extraction** (client.py:98-108)
- Decode JWT payload using stdlib (base64 + json, no PyJWT library)
- Extract from `sub` field with format `f:uuid:{customer_id}`
- Split on `:` and take last component

**Standard API Headers** (client.py:21-30)
All API requests require these headers to mimic the Android app:
```python
{
    "X-Tenant": "fraenk",
    "X-App-OS": "Android",
    "X-App-Device": "Python-Client",
    "X-App-Device-Vendor": "Python",
    "X-App-OS-Version": "13",
    "X-App-Version": "1.13.9"
}
```

### Testing with Fixtures
The CLI supports `--dry-run` mode (cli.py:46-54) which loads mock data from `fixtures/` directory:
- `fixtures/contracts.json` - Mock contract data
- `fixtures/data_consumption.json` - Mock consumption data
- No API calls made, no SMS required
- Useful for testing display logic without live credentials

## API Details

**Base URL**: `https://app.fraenk.de/fraenk-rest-service/app/v13`

**Key Endpoints**:
- `POST /login` - Initiate MFA login (returns mfa_token)
- `POST /login-with-mfa` - Complete login with SMS code
- `GET /customers/{customer_id}/contracts` - List contracts
- `GET /customers/{customer_id}/contracts/{contract_id}/dataconsumption` - Get usage data

**Important Notes**:
- HTTP 401 with `error: "mfa_required"` is the expected response for Step 1 (not an error)
- `Cache-Control: no-cache` header ensures fresh data (optional)
- API version is `/v13` - may require updates for future versions

## Library Usage

Can be imported and used programmatically:
```python
from fraenk_api import FraenkAPI

api = FraenkAPI()
mfa_response = api.login_initiate(username, password)
api.login_complete(username, password, sms_code, mfa_response["mfa_token"])
api.get_contracts()
data = api.get_data_consumption()
```

## Reverse Engineering Context

This project was created by decompiling the Fraenk Android APK (`de.congstar.fraenk_apkgk.apk`) with jadx. The decompiled source is in `sources/` directory:
- `sources/sa/InterfaceC2555a.java` - API service interfaces
- `sources/na/` - Request/response models

Key discoveries:
- Actual auth uses password + SMS MFA (not passwordless tokens)
- Customer ID extraction pattern from JWT `sub` field
- Required headers to mimic Android app

## Dependencies

Minimal dependency footprint:
- **requests**: Only external dependency for HTTP calls
- **stdlib only**: JWT decoding, base64, json, argparse
- **Python 3.13+**: Required version

## Documentation

- `docs/API.md` - Complete API endpoint documentation with request/response examples
- `docs/USAGE.md` - Installation guide, setup instructions, troubleshooting