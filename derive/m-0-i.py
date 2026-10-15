'''
Generates pre-HD era P2PKH (Pay-to-Public-Key-Hash) Bitcoin addresses.
This represents the original 2009 Bitcoin Core addresses before HD wallets (BIP32).
Derivation: m -> P2PKH (direct from master key)
'''
import json

from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicValidator,
    Bip32Secp256k1,
    Hash160,
    Base58Encoder,
)
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

# Example BIP39 mnemonic seed phrase
mnemonic, num_addresses = parse_derivation_arguments("Generate legacy P2PKH addresses from a BIP39 mnemonic.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)


def compute_p2pkh_address(pub_key_bytes):
    """Compute P2PKH address from public key bytes."""
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)


def compute_wif(private_key_bytes):
    """Encode a compressed mainnet private key in Wallet Import Format."""
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")


try:
    # Validate the mnemonic phrase
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")

    # Generate seed from mnemonic with passphrase
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)

    # Display the generated seed (in hex)

    # Generate BIP32 master key from seed
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)

    # Print the BIP32 Root Extended Public Key
    account_xpub = bip32_mst.PublicKey().ToExtended()
    account_xpriv = bip32_mst.PrivateKey().ToExtended()
    addresses = []


    # Generate a set number of addresses
    # for i in range(num_addresses):
    #     # Direct derivation from master key (m -> address)
    #     # For pre-HD, we use the master key directly
    #     address_key = bip32_mst

    #     # Construct derivation path
    #     derivation_path = f"m"
    for i in range(num_addresses):
        address_key = bip32_mst.ChildKey(0).ChildKey(i)
        derivation_path = f"m/0/{i}"

        address = compute_p2pkh_address(
            address_key.PublicKey().RawCompressed().ToBytes()
        )
        # Compute P2PKH address from the master key's public key
        address = compute_p2pkh_address(address_key.PublicKey().RawCompressed().ToBytes())
        public_key = address_key.PublicKey().RawCompressed().ToHex()
        private_key = address_key.PrivateKey().Raw().ToHex()
        # Bip32Slip10Secp256k1 has no ``to_wif`` method. Encode the raw
        # private key as a compressed, mainnet WIF instead.
        wif = compute_wif(address_key.PrivateKey().Raw().ToBytes())

        # Print the output in the specified order
        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})

    print(json.dumps({"mnemonic_phrase": mnemonic, "passphrase": passphrase, "seed_hex": seed_bytes.hex(), "address_type": "pre-HD P2PKH", "account_extended_public_key": account_xpub, "account_extended_private_key": account_xpriv, "addresses": addresses}, indent=2))

except MnemonicChecksumError as e:
    print(f"Error: Invalid mnemonic checksum. Details: {e}")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
