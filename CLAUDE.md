# Fraenk Mobile Data Tracking

## Project Overview
Python client for tracking mobile data consumption from Fraenk mobile service via reverse-engineered API.

## Status: ✅ Complete

Working Python API client with MFA authentication, data consumption tracking, and JSON export.

## What Was Built

### 1. Working API Client (`fraenk.py`)
- **MFA Authentication**: Two-step login with SMS verification
- **Data Consumption**: Fetch current usage, limits, and expiry
- **JSON Export**: Save full API responses with `--json` flag
- **Clean Architecture**: Modular code with helper functions

### 2. API Discovery Process
- Decompiled `de.congstar.fraenk_apkgk.apk` using jadx
- Found base API URL: `https://app.fraenk.de/fraenk-rest-service/app/v13`
- Located authentication endpoints in `/sources/sa/InterfaceC2555a.java`
- Discovered actual auth flow uses **password + SMS MFA**, not passwordless tokens

### 3. Authentication Flow (Corrected)

**Step 1: Initiate Login**
```
POST /login
Body: grant_type=password&username={email}&password={password}&scope=app
Response: 401 with mfa_token (SMS sent to phone)
```

**Step 2: Complete Login with MFA**
```
POST /login-with-mfa
Body: username={email}&password={password}&mtan={sms_code}&mfa_token={token}
Response: access_token, refresh_token
```

**JWT Token Processing:**
- Decode JWT payload (base64url) without verification
- Extract customer_id from `sub` field: `f:uuid:7555659511` → `7555659511`

### 4. Data Consumption Endpoint
```
GET /customers/{customer_id}/contracts/{contract_id}/dataconsumption
Header: Authorization: Bearer {access_token}
Header: Cache-Control: no-cache (optional, for fresh data)
```

**Response:**
```json
{
  "customer": {
    "msisdn": "0151 - 29489521",
    "contractType": "POST_PAID"
  },
  "passes": [
    {
      "passName": "Vertragsvolumen",
      "usedVolume": "5,17 GB",
      "usedBytes": 5560651713,
      "initialVolume": "25 GB",
      "percentageConsumption": 21,
      "expiryTimestamp": 1761951599000
    }
  ]
}
```

## Files Created

| File | Description |
|------|-------------|
| `src/fraenk_api/` | Main package directory |
| `src/fraenk_api/__init__.py` | Package initialization |
| `src/fraenk_api/__main__.py` | Entry point for python -m |
| `src/fraenk_api/client.py` | FraenkAPI class |
| `src/fraenk_api/cli.py` | CLI implementation |
| `src/fraenk_api/utils.py` | Helper functions |
| `.env.example` | Credentials template |
| `.gitignore` | Excludes `.env` |
| `docs/API.md` | Complete API documentation |
| `docs/USAGE.md` | Usage guide and examples |
| `pyproject.toml` | Project config with console script |

## Key Implementation Details

### Security
- Credentials loaded from `.env` file (gitignored)
- No external dependencies except `requests`
- JWT decoded with stdlib (base64 + json), no PyJWT needed
- MFA required for every login

### Architecture Decisions
- Proper Python package structure using src layout
- Modular design: separate client, CLI, and utils modules
- Console script entry point (`fraenk` command)
- Type hints throughout
- Can be used as library by importing `from fraenk_api import FraenkAPI`

## Usage

```bash
# Basic usage (pretty output)
uv run fraenk

# Or use python -m
uv run python -m fraenk_api

# JSON output to stdout
uv run fraenk -j

# Quiet mode
uv run fraenk -q
```

## Lessons Learned

1. **CLAUDE.md was wrong** - Documented "passwordless auth" was for password reset, not login
2. **JWT decoding simple** - No need for PyJWT library, stdlib base64 + json sufficient
3. **MFA always required** - HTTP 401 with `mfa_required` is success, not error
4. **Customer ID extraction** - JWT `sub` field has format `f:uuid:number`, extract last part
5. **API versioning** - Using `/app/v13`, may need updates for future versions

## Reverse Engineering Process

1. Decompiled APK with jadx
2. Found API service interfaces in `sources/sa/`
3. Identified request/response models in `sources/na/`
4. Tested endpoints with real credentials
5. Debugged error responses to understand flow
6. Documented working implementation

## Next Steps (Future)

- [ ] Token refresh implementation (use `refresh_token`)
- [ ] Session persistence (save tokens to file)
- [ ] Historical data tracking (store JSON exports over time)
- [ ] Data visualization (plot usage over time)
- [ ] Alerting (notify when approaching limit)

## Related Documentation

- Full API reference: `docs/API.md`
- Usage guide: `docs/USAGE.md`
- Decompiled source: `sources/` directory