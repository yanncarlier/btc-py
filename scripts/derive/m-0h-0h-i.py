'''
Derives from Bitcoin Core base with non-hardened third-level index.
Path: m/0'/0'/i  (e.g., m/0'/0'/0, m/0'/0'/1, m/0'/0'/2)
'''
import json
from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator, Bip32Secp256k1, Hash160, Base58Encoder
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

mnemonic, num_addresses = parse_derivation_arguments("Generate P2PKH with base m/0'/0'/i (non-hardened third-level index).")
passphrase = ""

def compute_p2pkh_address(pub_key_bytes):
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)

def compute_wif(private_key_bytes):
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")

try:
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase.")
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)
    account_xpub = None
    addresses = []
    # Base: m/0'/0'
    base = bip32_mst.ChildKey(0x80000000).ChildKey(0x80000000)
    for i in range(num_addresses):
        # Non-hardened index at third level
        address_key = base.ChildKey(i)
        if i == 0:
            account_xpub = address_key.PublicKey().ToExtended()
            account_xpriv = address_key.PrivateKey().ToExtended()
        derivation_path = f"m/0'/0'/{i}"
        address = compute_p2pkh_address(address_key.PublicKey().RawCompressed().ToBytes())
        public_key = address_key.PublicKey().RawCompressed().ToHex()
        private_key = address_key.PrivateKey().Raw().ToHex()
        wif = compute_wif(address_key.PrivateKey().Raw().ToBytes())
        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})
    print(json.dumps({
        "mnemonic_phrase": mnemonic,
        "passphrase": passphrase,
        "seed_hex": seed_bytes.hex(),
        "address_type": "P2PKH base m/0'/0'/i (non-hardened index)",
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
