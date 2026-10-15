"""Look up a Bitcoin address through Smartbit's public API.

.. warning::
    Smartbit (api.smartbit.com.au) is **permanently offline** as of 2022.
    This script raises a ``RuntimeError`` on every invocation to make that
    explicit.  The file is kept alongside the other ``explorers/``
    scripts for reference and completeness.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Return a Bitcoin address balance in satoshis from Smartbit. "
            "NOTE: Smartbit (api.smartbit.com.au) is permanently offline."
        )
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    return parser


def get_address_balance(address: str) -> int:  # noqa: ARG001
    """Raise an error because the Smartbit service is permanently offline.

    The Smartbit block explorer and API (api.smartbit.com.au) was shut down
    in 2022 and is no longer accessible.

    Args:
        address: Bitcoin address (unused; kept for API consistency).

    Raises:
        RuntimeError: Always, because Smartbit is permanently offline.
    """
    raise RuntimeError(
        "Smartbit (api.smartbit.com.au) is permanently offline and cannot be queried."
    )


def main() -> int:
    """Parse arguments and report that Smartbit is unavailable."""
    args = build_parser().parse_args()
    address = args.address.strip()

    if not address:
        print("Error: address must not be empty.", file=sys.stderr)
        return 2

    try:
        balance = get_address_balance(address)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(balance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

