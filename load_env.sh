#!/bin/bash
# Helper script to load credentials from .env or ~/.config/fraenk/credentials
# Usage: source load_env.sh

# Try ~/.config/fraenk/credentials first (preferred location)
if [ -f "$HOME/.config/fraenk/credentials" ]; then
    set -a
    source "$HOME/.config/fraenk/credentials"
    set +a
    echo "Loaded credentials from ~/.config/fraenk/credentials"
# Fall back to .env in current directory
elif [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "Loaded credentials from .env"
else
    echo "No credentials file found. Checked:"
    echo "  - ~/.config/fraenk/credentials"
    echo "  - ./.env"
    echo ""
    echo "Create one of these files with:"
    echo "  FRAENK_USERNAME=your_phone_number"
    echo "  FRAENK_PASSWORD=your_password"
fi
