'''
Generates BIP84 (Native SegWit P2WPKH) Addresses with hardened address index:
m/84'/0'/0'/0/{i}'
'''
import json

from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicValidator,
    Bip32Secp256k1,
    Bip84,
    Bip84Coins,
    Hash160,
    Base58Encoder,
    SegwitBech32Encoder,
)
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

mnemonic, num_addresses = parse_derivation_arguments("Generate BIP84 native SegWit P2WPKH addresses with hardened index m/84'/0'/0'/0/{i}'.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)

HARDENED_OFFSET = 0x80000000


def compute_p2wpkh(pub_key_bytes):
    # BIP84: native SegWit P2WPKH (bech32, witness version 0)
    # Witness program = Hash160 of the compressed public key
    key_hash = Hash160.QuickDigest(pub_key_bytes)
    return SegwitBech32Encoder.Encode("bc", 0, key_hash)


def compute_wif(private_key_bytes):
    # Mainnet WIF for a compressed public key: 0x80 + key + 0x01
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")


try:
    # Validate the mnemonic phrase
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")
    if num_addresses > HARDENED_OFFSET:
        raise ValueError("Number of addresses exceeds the maximum hardened index range.")

    # Generate seed from mnemonic with passphrase
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)

    # Account-level extended keys at m/84'/0'/0' (zpub / zprv), same as the non-hardened script
    bip84_mst_ctx = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
    bip84_acc_ctx = bip84_mst_ctx.Purpose().Coin().Account(0)
    account_xpub = bip84_acc_ctx.PublicKey().ToExtended()
    account_xpriv = bip84_acc_ctx.PrivateKey().ToExtended()

    # Manual BIP32 derivation down to the external chain: m/84'/0'/0'/0
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)
    base_ctx = (
        bip32_mst
        .ChildKey(HARDENED_OFFSET + 84)  # 84'
        .ChildKey(HARDENED_OFFSET + 0)   # 0'
        .ChildKey(HARDENED_OFFSET + 0)   # 0'
        .ChildKey(0)                     # 0 (external chain)
    )

    addresses = []

    # Generate a set number of hardened BIP84 addresses
    for i in range(num_addresses):
        # Hardened address index: m/84'/0'/0'/0/i'
        addr_ctx = base_ctx.ChildKey(HARDENED_OFFSET + i)
        derivation_path = f"m/84'/0'/0'/0/{i}'"

        pub_key_bytes = addr_ctx.PublicKey().RawCompressed().ToBytes()
        priv_key_bytes = addr_ctx.PrivateKey().Raw().ToBytes()

        address = compute_p2wpkh(pub_key_bytes)  # Native SegWit address (P2WPKH)
        public_key = addr_ctx.PublicKey().RawCompressed().ToHex()
        private_key = addr_ctx.PrivateKey().Raw().ToHex()  # Private key in hex
        wif = compute_wif(priv_key_bytes)  # Private key in WIF format

        addresses.append({
            "index": i,
            "derivation_path": derivation_path,
            "address": address,
            "public_key": public_key,
            "private_key": private_key,
            "wif": wif,
        })

    print(json.dumps({
        "mnemonic_phrase": mnemonic,
        "passphrase": passphrase,
        "seed_hex": seed_bytes.hex(),
        "address_type": "BIP84 P2WPKH hardened index",
        "account_extended_public_key": account_xpub,
        "account_extended_private_key": account_xpriv,
        "addresses": addresses
    }, indent=2))

except MnemonicChecksumError as e:
    print(f"Error: Invalid mnemonic checksum. Details: {e}")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")