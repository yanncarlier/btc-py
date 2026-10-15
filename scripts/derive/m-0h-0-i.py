'''
Generates legacy P2PKH (Pay-to-Public-Key-Hash) Bitcoin address.
BIP32 itself doesn’t specify a purpose but is often used directly for custom paths.
'''
import json

from mnemonic import Mnemonic
from bip32utils import BIP32Key, BIP32_HARDEN
from derivation_cli import parse_derivation_arguments

# Example BIP39 mnemonic seed phrase
mnemonic, num_addresses = parse_derivation_arguments("Generate MultiBit Classic-style P2PKH addresses from a BIP39 mnemonic.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)

try:
    # Initialize Mnemonic object for English wordlist
    mnemo = Mnemonic("english")

    # Validate the mnemonic phrase
    if not mnemo.check(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")


    # Convert mnemonic to seed (with empty passphrase)
    seed = mnemo.to_seed(mnemonic, passphrase=passphrase)
    account_xpub = None
    addresses = []


    # Generate BIP32 root key from the seed
    root_key = BIP32Key.fromEntropy(seed)

    # Print the BIP32 Root Key
    # account_xpub = root_key.ExtendedKey()  
    # print("BIP32 Root Key:", account_xpub)



    # Generate a set number of addresses
    for i in range(num_addresses):
        # Derive Bitcoin address using BIP44 path: m/44'/0'/0'/0/i
        # Note: Original script used m/32', but BIP44 for Bitcoin uses 44'. Adjusted accordingly.
        address_key = (root_key
                       .ChildKey(0 + BIP32_HARDEN)  # Purpose (BIP44)
                       .ChildKey(0)
                       .ChildKey(i))                 # Address index

        if i == 0:
            # Print the BIP32 Extended Private Key
            # account_xpub = address_key.ExtendedKey()
            # print("BIP32 Extended Private Key:", account_xpub)

            # Print the BIP32 Extended Public Key (xpub)
            account_xpub = address_key.ExtendedKey(private=False)  # Set private=False to get xpub
            account_xpriv = address_key.ExtendedKey(private=True)
            pass

        # Extract required information
        derivation_path = f"m/0'/0/{i}"
        address = address_key.Address()
        public_key = address_key.PublicKey().hex()
        private_key = address_key.PrivateKey().hex()
        wif = address_key.WalletImportFormat()

        # Print the output in the specified order
        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})

    print(json.dumps({"mnemonic_phrase": mnemonic, "passphrase": passphrase, "seed_hex": seed.hex(), "address_type": "MultiBit Classic P2PKH", "account_extended_public_key": account_xpub, "account_extended_private_key": account_xpriv, "addresses": addresses}, indent=2))

except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
