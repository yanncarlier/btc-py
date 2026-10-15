'''
Generates Taproot (P2TR) addresses using BIP86, an implementation of Segregated Witness (BIP141) with Schnorr signatures (BIP340).
BIP86 specifies the derivation path m/86'/0'/0'/0/i for Taproot addresses.
'''
import json

from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicValidator,
    Bip86,
    Bip86Coins,
    Bip44Changes
)
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

# Example BIP39 mnemonic seed phrase
mnemonic, num_addresses = parse_derivation_arguments("Generate BIP86 Taproot P2TR addresses from a BIP39 mnemonic.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)

try:
    # Validate the mnemonic phrase
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")
    
    # Generate seed from mnemonic with passphrase
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)

    # Display the generated seed (in hex)

    # Initialize BIP86 for Bitcoin mainnet and derive the default account (m/86'/0'/0')
    bip86_mst_ctx = Bip86.FromSeed(seed_bytes, Bip86Coins.BITCOIN)
    bip86_acc_ctx = bip86_mst_ctx.Purpose().Coin().Account(0)

    # Print the Account Extended Public Key
    account_xpub = bip86_acc_ctx.PublicKey().ToExtended()
    account_xpriv = bip86_acc_ctx.PrivateKey().ToExtended()
    addresses = []

    # Generate a set number of BIP86 addresses (Taproot, enabled by BIP341)
    for i in range(num_addresses):
        # Derive the external chain and address at index i
        bip86_chg_ctx = bip86_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
        bip86_addr_ctx = bip86_chg_ctx.AddressIndex(i)

        # Construct derivation path manually (BIP86: m/86'/0'/0'/i)
        derivation_path = f"m/86'/0'/0'/{i}"

             # Print the BIP32 Extended Public Key (xpub) when i == 0
        # if i == 0:
        #     bip32_xpub = bip86_chg_ctx.PublicKey().ToExtended()
        #     print("BIP32 Extended Public Key (xpub):", bip32_xpub)
               
        address = bip86_addr_ctx.PublicKey().ToAddress()  # Taproot address (starts with 'bc1p')
        public_key = bip86_addr_ctx.PublicKey().RawCompressed().ToHex()  # Compressed public key in hex
        private_key = bip86_addr_ctx.PrivateKey().Raw().ToHex()  # Private key in hex
        wif = bip86_addr_ctx.PrivateKey().ToWif()  # Private key in WIF format

        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})

    print(json.dumps({"mnemonic_phrase": mnemonic, "passphrase": passphrase, "seed_hex": seed_bytes.hex(), "address_type": "BIP86 P2TR", "account_extended_public_key": account_xpub, "account_extended_private_key": account_xpriv, "addresses": addresses}, indent=2))

except MnemonicChecksumError as e:
    print(f"Error: Invalid mnemonic checksum. Details: {e}")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
