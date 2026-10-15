'''
BIP44 derivation with hardened index: m/44'/0'/0'/{i}'
''' 
import json
from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator, Bip32Secp256k1, Hash160, Base58Encoder
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

mnemonic, num_addresses = parse_derivation_arguments("Generate BIP44 P2PKH hardened index m/44'/0'/0'/{i}'")
passphrase = ""

def compute_p2pkh(pub_key_bytes):
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)

def compute_wif(private_key_bytes):
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")

try:
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase.")
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)
    base_ctx = bip32_mst.ChildKey(0x8000002C).ChildKey(0x80000000).ChildKey(0x80000000)
    account_xpub = base_ctx.PublicKey().ToExtended()
    account_xpriv = base_ctx.PrivateKey().ToExtended()
    addresses = []
    for i in range(num_addresses):
        addr_ctx = base_ctx.ChildKey(0x80000000 + i)
        derivation_path = f"m/44'/0'/0'/{i}'"
        address = compute_p2pkh(addr_ctx.PublicKey().RawCompressed().ToBytes())
        public_key = addr_ctx.PublicKey().RawCompressed().ToHex()
        private_key = addr_ctx.PrivateKey().Raw().ToHex()
        wif = compute_wif(addr_ctx.PrivateKey().Raw().ToBytes())
        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})
    print(json.dumps({
        "mnemonic_phrase": mnemonic,
        "passphrase": passphrase,
        "seed_hex": seed_bytes.hex(),
        "address_type": "BIP44 P2PKH (hardened index)",
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
