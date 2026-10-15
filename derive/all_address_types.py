import argparse
import json

from bip_utils import (
    Bip39SeedGenerator,
    Bip32Secp256k1,
    Bip39MnemonicValidator,
    P2PKHAddrEncoder,
    P2SHAddrEncoder,
    P2WPKHAddrEncoder,
    P2TRAddrEncoder,
    WifEncoder,
)
from bip_utils.utils.mnemonic import MnemonicChecksumError

DEFAULT_MNEMONIC = (
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon about"
)

HARDENED = 0x80000000
HARDENED_MARK = "'"

# Path templates, written in the same notation as the file names:
#   h  = hardened, i = address index, ih = hardened address index.
PATH_TEMPLATES: list[str] = [
    "m",                      # illustrative: master key only
    "m-0-i",
    "m-0h-i",
    "m-0h-0-i",
    "m-0h-0-ih",
    "m-0h-0-0h",
    "m-0h-0h-i",
    "m-0h-0h-ih",
    "m-0h-0h-0h",
    "m-44h-0h-0h-0",
    "m-44h-0h-0h-0-i",
    "m-44h-0h-0h-0-ih",
    "m-44h-0h-0h-i",
    "m-44h-0h-0h-ih",
    "m-49h-0h-0h-0-i",
    "m-49h-0h-0h-0-ih",
    "m-84h-0h-0h-0-i",    
    "m-84h-0h-0h-0-ih",
    "m-86h-0h-0h-i",
]


def parse_template(template: str) -> list[tuple[str, bool]]:
    """Turn 'm-44h-0h-0h-0-ih' into [('44', True), ('0', True), ..., ('i', True)]."""
    tokens = template.split("-")[1:]  # drop leading 'm'
    parsed: list[tuple[str, bool]] = []
    for tok in tokens:
        if tok == "i":
            parsed.append(("i", False))
        elif tok == "ih":
            parsed.append(("i", True))
        elif tok.endswith("h"):
            parsed.append((tok[:-1], True))
        else:
            parsed.append((tok, False))
    return parsed


def address_type_for(template: str) -> str:
    """Pick the address type from the purpose (first path element)."""
    parts = template.split("-")
    purpose = parts[1] if len(parts) > 1 else ""
    return {"49h": "p2sh-p2wpkh", "84h": "p2wpkh", "86h": "p2tr"}.get(purpose, "p2pkh")


def encode_address(pub_key_bytes: bytes, addr_type: str) -> str:
    """Encode a compressed public key as a mainnet Bitcoin address."""
    if addr_type == "p2sh-p2wpkh":
        return P2SHAddrEncoder.EncodeKey(pub_key_bytes, net_ver=b"\x05")
    if addr_type == "p2wpkh":
        return P2WPKHAddrEncoder.EncodeKey(pub_key_bytes, hrp="bc")
    if addr_type == "p2tr":
        return P2TRAddrEncoder.EncodeKey(pub_key_bytes, hrp="bc")
    return P2PKHAddrEncoder.EncodeKey(pub_key_bytes, net_ver=b"\x00")


def derive_node(root, elements: list[tuple[str, bool]], index: int | None):
    """Walk the path from the root, substituting the index where 'i' appears."""
    node = root
    path = "m"
    for value, hardened in elements:
        n = index if value == "i" else int(value)
        node = node.ChildKey(n + HARDENED if hardened else n)
        mark = HARDENED_MARK if hardened else ""
        path += f"/{n}{mark}"
    return node, path


def build_group(root, template: str, count: int) -> dict:
    """Build the output group for one path template."""
    elements = parse_template(template)
    addr_type = address_type_for(template)
    has_index = any(v == "i" for v, _ in elements)

    addresses = []
    indices = range(count) if has_index else [None]
    for i in indices:
        node, path = derive_node(root, elements, i)
        pub = node.PublicKey().RawCompressed().ToBytes()
        priv = node.PrivateKey().Raw().ToBytes()
        addresses.append({
            "index": i,
            "derivation_path": path,
            "address_type": addr_type,
            "address": encode_address(pub, addr_type),
            "public_key": pub.hex(),
            "private_key": priv.hex(),
            "wif": WifEncoder.Encode(priv),
        })

    return {
        "template": template,
        "address_type": addr_type,
        "pattern": template.replace("-", "/").replace("ih", "i'").replace("h", "'"),
        "addresses": addresses,
    }


def main() -> None:
    """Generate Bitcoin addresses for all configured derivation paths."""
    parser = argparse.ArgumentParser(
        description="Generate Bitcoin addresses from a BIP39 mnemonic."
    )
    parser.add_argument(
        "values",
        nargs="*",
        metavar="COUNT_OR_MNEMONIC",
        help=(
            "Optional quoted mnemonic, or COUNT followed by an optional quoted "
            "mnemonic. If omitted, uses a default test phrase."
        ),
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=None,
        metavar="COUNT",
        help="Number of sequential addresses per path template (default: 1).",
    )
    args = parser.parse_args()

    count: int = args.count if args.count is not None else 1
    mnemonic = DEFAULT_MNEMONIC
    values: list[str] = args.values

    if len(values) == 1:
        if values[0].lstrip("+-").isdigit():
            if args.count is not None:
                parser.error("Specify the address count only once: as COUNT or with --count.")
            count = int(values[0])
        else:
            mnemonic = values[0]
    elif len(values) == 2:
        if not values[0].lstrip("+-").isdigit():
            parser.error("When supplying two positional arguments, the first must be COUNT.")
        if args.count is not None:
            parser.error("Specify the address count only once: as COUNT or with --count.")
        count = int(values[0])
        mnemonic = values[1]
    elif len(values) > 2:
        parser.error("Use an optional COUNT and one quoted mnemonic phrase.")

    if count < 1:
        parser.error("count must be a positive integer.")

    mnemonic = mnemonic.strip()

    try:
        Bip39MnemonicValidator().Validate(mnemonic)
    except MnemonicChecksumError as err:
        raise ValueError(
            "Invalid mnemonic phrase. Please provide a valid BIP39 mnemonic (12 or 24 words)."
        ) from err

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    root = Bip32Secp256k1.FromSeed(seed_bytes)

    output = [build_group(root, template, count) for template in PATH_TEMPLATES]
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()