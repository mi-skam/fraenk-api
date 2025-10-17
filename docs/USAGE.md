# Fraenk API Client - Usage Guide

## Installation

### Prerequisites
- Python 3.13+
- uv (recommended) or pip

### Installation Methods

Choose the installation method that fits your use case:

#### Method 1: Quick Start (Project-Based)

Best for: Trying out the tool, no installation needed

```bash
# Clone the project
git clone <repo-url>
cd fraenk

# Configure credentials
cp .env.example .env
# Edit .env with your credentials

# Sync dependencies
uv sync

# Run directly
uv run fraenk
```

**Pros**: No installation, isolated to project
**Cons**: Must use `uv run` prefix, must be in project directory

#### Method 2: Development Install (Editable)

Best for: Active development, code changes reflect immediately

```bash
# After cloning and setting up .env (see Method 1)
uv sync

# Install in editable mode
uv pip install -e .

# Activate virtual environment
source .venv/bin/activate

# Run without prefix
fraenk
```

**Pros**: Code changes take effect immediately, no `uv run` needed when venv active
**Cons**: Need to activate venv, or use full path `.venv/bin/fraenk`

#### Method 3: Global Tool Install (Recommended for Daily Use)

Best for: Using as a regular command-line tool

```bash
# After cloning and setting up .env (see Method 1)

# Install as global tool
uv tool install .

# Run from anywhere
fraenk
```

**Pros**: Available globally, no activation needed, isolated environment
**Cons**: Need to reinstall after code changes

**Updating after code changes:**
```bash
uv tool install --reinstall .
```

**Uninstall:**
```bash
uv tool uninstall fraenk
```

#### Alternative: Using pipx

If you prefer `pipx` over `uv tool`:

```bash
pipx install .           # Install
pipx install --force .   # Reinstall after changes
pipx uninstall fraenk    # Uninstall
```

Both `uv tool` and `pipx` work identically - use whichever you prefer.

### Configure Credentials

**All methods require a `.env` file in the project root:**

```bash
cp .env.example .env
```

Edit `.env` with your Fraenk credentials:
```
FRAENK_USERNAME=your_email@example.com
FRAENK_PASSWORD=your_password
```

### Installation Methods Comparison

| Method | Command Available | Environment | Code Changes | Use Case |
|--------|------------------|-------------|--------------|----------|
| `uv run fraenk` | In project dir only | Project's .venv | Immediate | Quick testing |
| Editable install | When venv active | Project's .venv | Immediate | Active development |
| `uv tool install` | Globally | Isolated by uv | Needs reinstall | Daily use (stable) |
| `pipx install` | Globally | Isolated by pipx | Needs reinstall | Daily use (stable) |

## Usage

### Basic Usage

Run the CLI to check your data consumption:

```bash
# If installed globally (uv tool install or pipx install)
fraenk

# If using project-based (uv run)
uv run fraenk

# Or using python -m
uv run python -m fraenk_api

# If editable install (when venv is activated)
fraenk
```

The examples below use `uv run fraenk`, but you can replace with just `fraenk` if you installed globally or activated the venv.

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

### JSON Output

To output raw JSON to stdout (Unix-style, pipeable):

```bash
uv run fraenk --json
# or short form
uv run fraenk -j
```

**JSON mode behavior:**
- Outputs only raw JSON to stdout (no progress messages)
- Can be piped to `jq` or other tools
- Can be redirected to a file

**Examples:**

```bash
# Pretty-print with jq
uv run fraenk -j | jq

# Save to file
uv run fraenk -j > data.json

# Extract specific field
uv run fraenk -j | jq '.customer.msisdn'

# Get used bytes
uv run fraenk -j | jq '.passes[0].usedBytes'
```

**JSON output includes:**
- Customer information (phone number, contract type)
- All data passes with detailed usage
- Raw byte values for precise calculations
- Timestamps for expiry and last update
- Additional metadata from the API

### Quiet Mode

To suppress progress messages while keeping the pretty table:

```bash
uv run fraenk --quiet
# or short form
uv run fraenk -q
```

This hides "Fetching contracts..." and similar messages but still shows the formatted output.

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--json` | `-j` | Output raw JSON to stdout (pipeable) |
| `--quiet` | `-q` | Suppress progress messages (pretty mode only) |
| `--help` | `-h` | Show help message and exit |

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
from fraenk_api import FraenkAPI

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
| `src/fraenk_api/` | Main package directory |
| `src/fraenk_api/client.py` | FraenkAPI class |
| `src/fraenk_api/cli.py` | CLI implementation |
| `src/fraenk_api/utils.py` | Helper functions |
| `.env` | Your credentials (create from `.env.example`) |
| `.env.example` | Template for credentials |
| `docs/API.md` | API documentation |
| `docs/USAGE.md` | This file |

## Support

This is an unofficial API client. For Fraenk account issues, contact Fraenk support:
- Website: https://www.fraenk.de
- Support: Via Fraenk app

For issues with this script, check the README or source code.
