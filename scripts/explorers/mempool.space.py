"""Look up a Bitcoin address through Mempool Space's public API."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
from urllib.parse import quote


API_HOST = "mempool.space"
REQUEST_TIMEOUT_SECONDS = 15


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Return a Bitcoin address's total balance in satoshis from Mempool Space."
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    return parser


def get_address_balance(address: str) -> int:
    """Request and return Mempool Space's total balance for one address.

    Args:
        address: Bitcoin address to include in the API request path.

    Returns:
        The confirmed and unconfirmed balance in satoshis.

    Raises:
        RuntimeError: If the API returns a non-success response.
        OSError: If the network request cannot be completed.
    """
    encoded_address = quote(address, safe="")
    connection = http.client.HTTPSConnection(API_HOST, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        connection.request("GET", f"/api/address/{encoded_address}")
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    if response.status != http.HTTPStatus.OK:
        raise RuntimeError(
            f"Mempool Space returned HTTP {response.status} {response.reason}: {response_body}"
        )

    try:
        address_details = json.loads(response_body)
        chain_stats = address_details["chain_stats"]
        mempool_stats = address_details["mempool_stats"]
        balance = (
            chain_stats["funded_txo_sum"]
            - chain_stats["spent_txo_sum"]
            + mempool_stats["funded_txo_sum"]
            - mempool_stats["spent_txo_sum"]
        )
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError("Mempool Space returned an unexpected balance response.") from error

    if not isinstance(balance, int):
        raise RuntimeError("Mempool Space returned a non-integer balance.")

    return balance


def main() -> int:
    """Parse arguments, fetch the total balance, and print it in satoshis."""
    args = build_parser().parse_args()
    address = args.address.strip()

    if not address:
        print("Error: address must not be empty.", file=sys.stderr)
        return 2

    try:
        balance = get_address_balance(address)
    except (OSError, http.client.HTTPException, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(balance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
