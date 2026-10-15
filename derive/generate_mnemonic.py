# https://github.com/trezor/python-mnemonic
import json
import argparse
from mnemonic import Mnemonic
import bip32utils  # Ensure you have this library installed

def main():
    parser = argparse.ArgumentParser(description="Generate a BIP39 mnemonic, seed, and BIP32 root key.")
    parser.add_argument(
        "-s", "--strength",
        type=int,
        choices=[128, 160, 192, 224, 256],
        default=128,
        help="Strength of the mnemonic in bits (default: 128 for 12 words, use 256 for 24 words)"
    )
    args = parser.parse_args()

    mnemonic = Mnemonic("english")
    
    # Generate word list given the strength (128 - 256):
    words = mnemonic.generate(strength=args.strength)
    
    # Given the word list generate seed:
    seed = mnemonic.to_seed(words)
    
    # Generate BIP32 Root Key:
    bip32_root_key = bip32utils.BIP32Key.fromEntropy(seed)
    
    output = {
        "bip39_mnemonic": words,
        "bip39_seed": seed.hex(),
        "bip32_root_key": bip32_root_key.ExtendedKey()
    }
    
    print(json.dumps(output, indent=4))

if __name__ == "__main__":
    main()
