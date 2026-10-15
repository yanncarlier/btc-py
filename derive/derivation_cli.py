"""Shared command-line arguments for the individual address derivation scripts."""

from __future__ import annotations

import argparse


DEFAULT_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"


def positive_count(value: str) -> int:
    """Parse an address count that is greater than zero."""
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("number of addresses must be at least 1")
    return count


def is_positive_integer(value: str) -> bool:
    """Check if a string represents a positive integer."""
    try:
        return int(value) > 0
    except ValueError:
        return False


def parse_derivation_arguments(description: str) -> tuple[str, int]:
    """Return the BIP39 mnemonic and address count supplied by the user.

    Supports the following usage patterns:
    - script.py                     : default mnemonic, 1 address
    - script.py 5                   : default mnemonic, 5 addresses
    - script.py "mnemonic words"   : custom mnemonic, 1 address
    - script.py "mnemonic words" 5 : custom mnemonic, 5 addresses
    - script.py -n 5                : default mnemonic, 5 addresses
    - script.py -n 5 "mnemonic"     : custom mnemonic, 5 addresses
    """
    import sys

    # Handle the case where first arg is a bare number (for count)
    # This allows: script.py 5
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-') and is_positive_integer(sys.argv[1]):
        # First argument is a bare positive integer, treat as count
        count = positive_count(sys.argv[1])
        mnemonic = DEFAULT_MNEMONIC
        # If there's a second argument and it doesn't start with -, it's the mnemonic
        if len(sys.argv) >= 3 and not sys.argv[2].startswith('-'):
            mnemonic = sys.argv[2]
        return mnemonic, count

    # Handle the case where first arg is a mnemonic and second arg is a number
    # This allows: script.py "mnemonic words" 5
    if len(sys.argv) >= 3 and not sys.argv[1].startswith('-') and not sys.argv[2].startswith('-') and is_positive_integer(sys.argv[2]):
        mnemonic = sys.argv[1]
        count = positive_count(sys.argv[2])
        return mnemonic, count

    # Use argparse for all other cases (including --help, -n, etc.)
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-n", "--count",
        type=positive_count,
        default=1,
        help="number of addresses to derive (default: 1)",
    )
    parser.add_argument(
        "mnemonic",
        nargs="?",
        default=DEFAULT_MNEMONIC,
        help="quoted 12- or 24-word BIP39 mnemonic; defaults to the public test mnemonic",
    )
    arguments = parser.parse_args()
    return arguments.mnemonic, arguments.count
