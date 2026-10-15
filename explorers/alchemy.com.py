"""Look up a Bitcoin address balance through Alchemy.

.. warning::
    Alchemy's Bitcoin API (https://www.alchemy.com/) is a **JSON-RPC node
    relay** that mirrors the standard Bitcoin Core RPC interface
    (``getblock``, ``getrawtransaction``, ``gettxout``, etc.).  Bitcoin Core
    deliberately does **not** index the blockchain by address, so there is no
    method to query the balance of an arbitrary address through this API.

    This script raises a ``RuntimeError`` on every invocation to make that
    limitation explicit.  The file is kept alongside the other
    ``explorers/`` scripts for reference and completeness.

    If you need address-based balance lookups with an API key-gated service,
    see ``cryptoapis.io.py`` instead.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Return a Bitcoin address balance from Alchemy. "
            "NOTE: Alchemy's Bitcoin API is a JSON-RPC node relay and does "
            "not support address balance lookups."
        )
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    return parser


def get_address_balance(address: str) -> int:  # noqa: ARG001
    """Raise an error because Alchemy cannot look up address balances.

    Alchemy's Bitcoin API exposes only standard Bitcoin Core JSON-RPC methods
    (e.g. ``getblock``, ``getrawtransaction``).  Bitcoin Core does not index
    the chain by address, so there is no RPC method that returns the balance
    of an arbitrary address.

    Args:
        address: Bitcoin address (unused; kept for API consistency).

    Raises:
        RuntimeError: Always, because address balance lookups are unsupported.
    """
    raise RuntimeError(
        "Alchemy's Bitcoin API is a JSON-RPC node relay that does not "
        "support address balance lookups.  Use a block-explorer API such as "
        "Blockstream, Mempool.space, or CryptoAPIs instead."
    )


def main() -> int:
    """Parse arguments and report that Alchemy cannot look up address balances."""
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

