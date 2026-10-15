#!/usr/bin/env python3
"""
sweep.py: Programmatically transfer all bitcoin from a private key to a destination address.
"""

import sys
import argparse
from bit import PrivateKeyTestnet, PrivateKey


def sweep_funds(wif_key: str, destination_address: str, testnet: bool = False):
    """Sweeps all funds from a private key to a destination address."""
    try:
        # Select network type
        key_class = PrivateKeyTestnet if testnet else PrivateKey
        my_key = key_class(wif_key)

        print(f"Source Address: {my_key.address}")
        print(f"Destination Address: {destination_address}")

        # Check balance before sweeping
        balance_satoshis = my_key.get_balance()
        print(f"Current Balance: {balance_satoshis} satoshis")

        if int(balance_satoshis) <= 0:
            print("Error: The address has a zero or negative balance.")
            sys.exit(1)

        # Send all funds (subtracting fee automatically)
        # send() takes a list of tuples: (destination_address, amount, currency_unit)
        # Using 'satoshi' and 'all' ensures the entire balance minus fee is sent.
        tx_hash = my_key.send([(destination_address, "all", "satoshi")])

        print("Transaction successfully broadcasted!")
        print(f"Transaction Hash: {tx_hash}")

    except Exception as e:
        print(f"An error occurred during the sweep: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Programmatically transfer all bitcoin from a private key to a destination address.")
    parser.add_argument("wif_key", help="The WIF format private key of the source address")
    parser.add_argument("dest_address", help="The destination Bitcoin address")
    parser.add_argument("--testnet", action="store_true", help="Use testnet instead of mainnet")
    args = parser.parse_args()

    sweep_funds(args.wif_key, args.dest_address, testnet=args.testnet)