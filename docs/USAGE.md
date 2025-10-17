# Fraenk API Client - Usage Guide

## Prerequisites & Setup

### Prerequisites
- Python 3.13+
- uv (recommended) or pip

### Initial Setup

First, clone the project and configure credentials:

```bash
# Clone the project
git clone <repo-url>
cd fraenk

# Configure credentials
cp .env.example .env
# Edit .env with your credentials
```

Edit `.env` with your Fraenk credentials:
```
FRAENK_USERNAME=your_email@example.com
FRAENK_PASSWORD=your_password
```

## Installation Methods

Choose the installation method that fits your use case:

#### Method 1: Quick Start (Project-Based)
```bash
# Run directly (after setup above)
uv run fraenk
```

#### Method 2: Development Install (Editable)
```bash
# Install in editable mode (after setup above)
uv pip install -e .

# Activate virtual environment
source .venv/bin/activate

# Run without prefix
fraenk
```

#### Method 3: Global Tool Install (Recommended for Daily Use)

```bash
# Install as global tool (after setup above)
uv tool install .

# Run from anywhere
fraenk
```

**Updating after code changes:**
```bash
uv tool install --reinstall .
```

**Uninstall:**
```bash
uv tool uninstall fraenk
```

## Usage

### Basic Usage

Run the CLI to check your data consumption:

```bash
fraenk # or uv run fraenk
```

**Interactive flow:**
1. Script initiates login and sends SMS code to your phone
2. Enter the 6-digit SMS code when prompted
3. View your data consumption

**Example output:**
```
==================================================
📱 FRAENK DATA CONSUMPTION
==================================================
Phone: 0151 - 29489521

📊 Vertragsvolumen
   Used: 5,17 GB / 25 GB (21%)
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
fraenk -j | jq

# Save to file
fraenk -j > data.json

# Extract specific field
fraenk -j | jq '.customer.msisdn'
```

### Quiet Mode

To suppress progress messages while keeping the pretty table:

```bash
fraenk --quiet
# or short form
fraenk -q
```

This hides "Fetching contracts..." and similar messages but still shows the formatted output.

### Dry Run Mode

For testing without making API calls or requiring SMS codes:

```bash
fraenk --dry-run
# or short form
fraenk -d
```

This uses mock data from the `fixtures/` directory, useful for testing display logic without live credentials.

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--json` | `-j` | Output raw JSON to stdout (pipeable) |
| `--quiet` | `-q` | Suppress progress messages (pretty mode only) |
| `--dry-run` | `-d` | Use mock data from fixtures (no API calls, no SMS required) |
| `--help` | `-h` | Show help message and exit |

## Environment Variables

The script uses the following environment variables (loaded from `.env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `FRAENK_USERNAME` | Yes | Your Fraenk account email |
| `FRAENK_PASSWORD` | Yes | Your Fraenk account password |

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

This is an unofficial API client. 

For issues with this script, check the README or source code.
