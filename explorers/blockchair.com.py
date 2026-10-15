"""Look up a Bitcoin address balance through Blockchair's public API."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
from urllib.parse import quote


API_HOST = "api.blockchair.com"
REQUEST_TIMEOUT_SECONDS = 15


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Return a Bitcoin address balance in satoshis from Blockchair."
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    return parser


def get_address_balance(address: str) -> int:
    """Request and return Blockchair's balance for one Bitcoin address.

    Uses the ``/bitcoin/addresses/balances`` endpoint, which returns the
    confirmed balance in satoshis.  Free-tier access has a rate limit; see
    https://blockchair.com/api/docs for details.

    Args:
        address: Bitcoin address to include in the API request query string.

    Returns:
        The confirmed balance in satoshis.

    Raises:
        RuntimeError: If the API returns a non-success response or an
            unexpected JSON structure.
        OSError: If the network request cannot be completed.
    """
    encoded_address = quote(address, safe="")
    connection = http.client.HTTPSConnection(API_HOST, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        connection.request(
            "GET",
            f"/bitcoin/addresses/balances?addresses={encoded_address}",
        )
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    if response.status != http.HTTPStatus.OK:
        raise RuntimeError(
            f"Blockchair returned HTTP {response.status} {response.reason}: {response_body}"
        )

    try:
        data = json.loads(response_body)["data"]
        # The endpoint returns {address: balance_in_satoshis, ...}.
        # An address with no on-chain activity may be absent from the mapping.
        balance = data.get(address, 0)
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError("Blockchair returned an unexpected balance response.") from error

    if not isinstance(balance, int):
        raise RuntimeError("Blockchair returned a non-integer balance.")

    return balance


def main() -> int:
    """Parse arguments, fetch the address balance, and print it in satoshis."""
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

