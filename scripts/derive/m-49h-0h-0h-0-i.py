'''
BIP49 external chain with non-hardened index: m/49'/0'/0'/0/{i}
'''
import json
from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator, Bip32Secp256k1, Hash160, Base58Encoder
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

mnemonic, num_addresses = parse_derivation_arguments("Generate BIP49 external chain index m/49'/0'/0'/0/{i}.")
passphrase = ""

def compute_p2sh_p2wpkh(pub_key_bytes):
    # BIP49: P2SH-wrapped P2WPKH
    # 1. Hash160 of the compressed public key
    key_hash = Hash160.QuickDigest(pub_key_bytes)
    # 2. Redeem script: OP_0 (0x00) + push 20 bytes (0x14) + key hash
    redeem_script = b"\x00\x14" + key_hash
    # 3. The address is Base58Check(0x05 + Hash160(redeem_script))
    script_hash = Hash160.QuickDigest(redeem_script)
    return Base58Encoder.CheckEncode(b"\x05" + script_hash)

def compute_wif(private_key_bytes):
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")

try:
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase.")
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)
    base_ctx = bip32_mst.ChildKey(0x80000031).ChildKey(0x80000000).ChildKey(0x80000000).ChildKey(0)
    account_xpub = base_ctx.PublicKey().ToExtended()
    account_xpriv = base_ctx.PrivateKey().ToExtended()
    addresses = []
    for i in range(num_addresses):
        addr_ctx = base_ctx.ChildKey(i)
        derivation_path = f"m/49'/0'/0'/0/{i}"
        address = compute_p2sh_p2wpkh(addr_ctx.PublicKey().RawCompressed().ToBytes())
        public_key = addr_ctx.PublicKey().RawCompressed().ToHex()
        private_key = addr_ctx.PrivateKey().Raw().ToHex()
        wif = compute_wif(addr_ctx.PrivateKey().Raw().ToBytes())
        addresses.append({"index": i, "derivation_path": derivation_path, "address": address, "public_key": public_key, "private_key": private_key, "wif": wif})
    print(json.dumps({
        "mnemonic_phrase": mnemonic,
        "passphrase": passphrase,
        "seed_hex": seed_bytes.hex(),
        "address_type": "BIP49 external chain index",
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