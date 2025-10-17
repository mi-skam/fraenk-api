# Fraenk API Client - Usage Guide

## Installation

### Prerequisites
- Python 3.13+
- uv (or pip)

### Setup

1. **Clone or download the project**

2. **Install dependencies:**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials:**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Fraenk credentials:
   ```
   FRAENK_USERNAME=your_email@example.com
   FRAENK_PASSWORD=your_password
   ```

## Usage

### Basic Usage

Run the script to check your data consumption:

```bash
python fraenk.py
```

**Interactive flow:**
1. Script initiates login and sends SMS code to your phone
2. Enter the 6-digit SMS code when prompted
3. View your data consumption

**Example output:**
```
Initiating login (MFA SMS will be sent)...
MFA response: Wir schicken dir einen 6-stelligen Bestätigungscode per SMS an deine Rufnummer mit den Endziffern *********521
Enter SMS code: 123456
Completing login with SMS code...
Login successful!

Fetching contracts...
Found 1 contract(s)
Fetching data consumption...

==================================================
📱 FRAENK DATA CONSUMPTION
==================================================
Phone: 0151 - 29489521
Contract: POST_PAID

--------------------------------------------------

📊 Vertragsvolumen
   Used: 5,17 GB / 25 GB
   Usage: 21%
   Expires: 2025-10-31 23:59

==================================================
```

### Save JSON Export

To save the complete API response as a JSON file:

```bash
python fraenk.py --json
```

This creates a timestamped file: `fraenk-api-YYYYMMDD-HHMM.json`

Example: `fraenk-api-20251017-0730.json`

**JSON output includes:**
- Customer information (phone number, contract type)
- All data passes with detailed usage
- Raw byte values for precise calculations
- Timestamps for expiry and last update
- Additional metadata from the API

## Command Line Options

| Option | Description |
|--------|-------------|
| `--json` | Save API response to JSON file with timestamp |

## Environment Variables

The script uses the following environment variables (loaded from `.env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `FRAENK_USERNAME` | Yes | Your Fraenk account email |
| `FRAENK_PASSWORD` | Yes | Your Fraenk account password |

## Security Notes

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **SMS verification required** - Every login requires SMS 2FA
3. **Credentials stored locally** - Only on your machine, never transmitted except to Fraenk API
4. **JSON exports gitignored** - Pattern `fraenk-api-*.json` is excluded from git

## Troubleshooting

### "FRAENK_USERNAME environment variable must be set"
- Make sure you created the `.env` file
- Check that credentials are in format: `KEY=value` (no spaces around `=`)

### "401 Client Error: Unauthorized"
- Check your username and password in `.env`
- Try resetting your password on the Fraenk website

### "404 Client Error: Not Found"
- This usually means the customer_id or contract_id extraction failed
- Report this as a bug with your error output

### SMS code not arriving
- Wait up to 2 minutes for SMS delivery
- Check your phone number is correct in your Fraenk account
- Try logging in via the official Fraenk app first

### ModuleNotFoundError
- Run `uv sync` to install dependencies
- Or `pip install requests`

## Advanced Usage

### Using as a Library

You can import and use the `FraenkAPI` class in your own scripts:

```python
from fraenk import FraenkAPI

api = FraenkAPI()

# Login (2-step MFA)
mfa_response = api.login_initiate("email@example.com", "password")
mfa_token = mfa_response["mfa_token"]

# User enters SMS code
sms_code = input("Enter SMS code: ")

# Complete login
api.login_complete("email@example.com", "password", sms_code, mfa_token)

# Get data consumption
api.get_contracts()
data = api.get_data_consumption()

print(data)
```

### Disable Cache

By default, the API uses cached data. To force fresh data:

```python
data = api.get_data_consumption(use_cache=False)
```

This sends `Cache-Control: no-cache` header to the API.

## Files

| File | Description |
|------|-------------|
| `fraenk.py` | Main script and API client |
| `.env` | Your credentials (create from `.env.example`) |
| `.env.example` | Template for credentials |
| `fraenk-api-*.json` | JSON exports (when using `--json`) |
| `docs/API.md` | API documentation |
| `docs/USAGE.md` | This file |

## Support

This is an unofficial API client. For Fraenk account issues, contact Fraenk support:
- Website: https://www.fraenk.de
- Support: Via Fraenk app

For issues with this script, check the README or source code.
