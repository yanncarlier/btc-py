"""Look up a Bitcoin address balance through Blockchain.com's public API."""

from __future__ import annotations

import argparse
import http.client
import sys
from urllib.parse import quote


API_HOST = "blockchain.info"
REQUEST_TIMEOUT_SECONDS = 15


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Return a Bitcoin address balance in satoshis from Blockchain.com."
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    return parser


def get_address_balance(address: str) -> str:
    """Request and return the API balance response for one Bitcoin address.

    Args:
        address: Bitcoin address to include in the API request path.

    Returns:
        The balance in satoshis, as returned by the API.

    Raises:
        RuntimeError: If the API returns a non-success response.
        OSError: If the network request cannot be completed.
    """
    encoded_address = quote(address, safe="")
    connection = http.client.HTTPSConnection(API_HOST, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        connection.request("GET", f"/q/addressbalance/{encoded_address}")
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    if response.status != http.HTTPStatus.OK:
        raise RuntimeError(
            f"Blockchain.com returned HTTP {response.status} {response.reason}: {response_body}"
        )

    return response_body


def main() -> int:
    """Parse arguments, fetch the address balance, and print it."""
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
