# Fraenk Mobile Data Tracker

Unofficial Python client for tracking mobile data consumption from Fraenk mobile service via reverse-engineered API.

## Quick Start

### Installation

```bash
# Configure credentials and edit .env with your Fraenk email and password
cp .env.example .env
```

### Usage

```bash
# Check data consumption (pretty output)
uv run fraenk

# Output JSON to stdout (pipeable)
uv run fraenk -j

```

### Example Output

```
==================================================
=� FRAENK DATA CONSUMPTION
==================================================
Phone: 01234 - 567890
Contract: POST_PAID

--------------------------------------------------

=� Vertragsvolumen
   Used: 5,17 GB / 25 GB
   Usage: 21%
   Expires: 2025-10-31 23:59

==================================================
```

## Documentation

- **[Usage Guide](docs/USAGE.md)** - Installation, setup, troubleshooting, and advanced usage
- **[API Documentation](docs/API.md)** - Complete API reference with endpoints and data models

## Requirements

- Python 3.13+
- Fraenk mobile account
- Access to SMS messages

## Project Structure

```
.
├── src/
│   └── fraenk_api/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Entry point for python -m
│       ├── client.py        # FraenkAPI class
│       ├── cli.py           # CLI logic
│       └── utils.py         # Helper functions
├── .env.example             # Credentials template
├── pyproject.toml           # Project configuration
└── docs/
    ├── API.md               # API documentation
    └── USAGE.md             # Usage guide
```

## Disclaimer

This is an **unofficial** API client created through reverse engineering. Not affiliated with Fraenk or Congstar.

- Use at your own risk
- API may change without notice
- For official support, use the Fraenk app or website

## License

MIT