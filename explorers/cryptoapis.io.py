"""Look up a Bitcoin address through CryptoAPIs' blockchain data REST API.

An API key is required.  Register for a free account at
https://cryptoapis.io/ and generate a key from the dashboard.

The key is read from the ``CRYPTO_APIS_KEY`` environment variable by
default, or supplied via the ``--api-key`` CLI flag.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from urllib.parse import quote


API_HOST = "rest.cryptoapis.io"
REQUEST_TIMEOUT_SECONDS = 15

# 1 BTC == 100_000_000 satoshis
_SATOSHIS_PER_BTC = 100_000_000


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Return a Bitcoin address's confirmed balance in satoshis from CryptoAPIs. "
            "Requires a CryptoAPIs API key (https://cryptoapis.io/)."
        )
    )
    parser.add_argument(
        "address",
        help="Bitcoin address to look up (for example, a bc1..., 1..., or 3... address).",
    )
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        default=None,
        help=(
            "CryptoAPIs API key.  Falls back to the CRYPTO_APIS_KEY "
            "environment variable when omitted."
        ),
    )
    return parser


def resolve_api_key(cli_value: str | None) -> str:
    """Return the API key from the CLI flag or the environment variable.

    Args:
        cli_value: Value passed via ``--api-key``, or ``None`` if omitted.

    Returns:
        The non-empty API key string.

    Raises:
        RuntimeError: If no key is found in either source.
    """
    key = cli_value or os.environ.get("CRYPTO_APIS_KEY", "")
    if not key:
        raise RuntimeError(
            "No API key provided.  Pass --api-key KEY or set the "
            "CRYPTO_APIS_KEY environment variable."
        )
    return key


def get_address_balance(address: str, api_key: str) -> int:
    """Request and return CryptoAPIs' confirmed balance for one address.

    Calls ``GET /blockchain-data/bitcoin/mainnet/addresses/{address}/balance``
    and converts the returned BTC amount string to satoshis.

    Args:
        address: Bitcoin address to include in the API request path.
        api_key: A valid CryptoAPIs API key sent in the ``x-api-key`` header.

    Returns:
        The confirmed balance in satoshis.

    Raises:
        RuntimeError: If the API returns a non-success response or an
            unexpected JSON structure.
        OSError: If the network request cannot be completed.
    """
    encoded_address = quote(address, safe="")
    path = f"/blockchain-data/bitcoin/mainnet/addresses/{encoded_address}/balance"
    connection = http.client.HTTPSConnection(API_HOST, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        connection.request(
            "GET",
            path,
            headers={"x-api-key": api_key},
        )
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    if response.status != http.HTTPStatus.OK:
        raise RuntimeError(
            f"CryptoAPIs returned HTTP {response.status} {response.reason}: {response_body}"
        )

    try:
        amount_str = json.loads(response_body)["data"]["item"]["confirmedBalance"]["amount"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(
            "CryptoAPIs returned an unexpected balance response."
        ) from error

    try:
        # The amount is expressed in BTC as a decimal string (e.g. "0.00153200").
        balance = int(Decimal(amount_str) * _SATOSHIS_PER_BTC)
    except (InvalidOperation, ValueError) as error:
        raise RuntimeError(
            f"CryptoAPIs returned an unrecognisable balance amount: {amount_str!r}"
        ) from error

    return balance


def main() -> int:
    """Parse arguments, fetch the confirmed balance, and print it in satoshis."""
    args = build_parser().parse_args()
    address = args.address.strip()

    if not address:
        print("Error: address must not be empty.", file=sys.stderr)
        return 2

    try:
        api_key = resolve_api_key(args.api_key)
        balance = get_address_balance(address, api_key)
    except (OSError, http.client.HTTPException, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(balance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

