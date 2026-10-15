# scripts

Educational Python scripts for Bitcoin address derivation, mnemonic generation, and blockchain queries.

## Account 1, Bitcoin donation addresses:

```
"address": "bc1qmr2sm7fmejfaqcd0l067m75c8c8h46kq5uw70g"
"address": "bc1qa3tjj9fc7n0j3lnfuc56tqdhlqrt0uw0czrkm6"
"address": "bc1qyu3zy7nasur5ju8hghs3kc3480h5rccs3fthfh"
```

---

## Setup

- Python 3.10+
- `uv` or `pip`

```bash
uv self update
uv venv && source .venv/bin/activate
uv sync
uv pip install -e ".[dev]"
```

---

## Derivation Scripts (renamed to `m-...` convention)

| New Filename | Derivation Path | Address Type | Era / Market |
|---|---|---|---|
| `derive/m-0-i.py` | `m/0/{i}` | Legacy P2PKH | Pre-HD (2009) |
| `derive/m-0h-i.py` | `m/0'/{i}` | Legacy P2PKH | Electrum-style (2011) |
| `derive/m-0h-0h-0h.py` | `m/0'/0'/0'` | Legacy P2PKH | Bitcoin Core HD (2012) |
| `derive/m-0h-0-i.py` | `m/0'/0/{i}` | Legacy P2PKH | MultiBit Classic |
| `derive/m-0h-0-0h.py` | `m/0'/0/0'` | Legacy P2PKH | MultiBit HD |
| `derive/m-44h-0h-0h-i.py` | `m/44'/0'/0'/0/n` | Legacy P2PKH | BIP44 (2014) |
| `derive/m-44h-0h-0h-0.py` | `m/44'/0'/0'/0` | Chain-level P2PKH | BIP44 external chain |
| `derive/m-49h-0h-0h-i.py` | `m/49'/0'/0'/0/n` | Wrapped SegWit (P2SH-P2WPKH) | BIP49 (2016) |
| `derive/m-84h-0h-0h-i.py` | `m/84'/0'/0'/0/n` | Native SegWit (P2WPKH) | BIP84 (2017) |
| `derive/m-86h-0h-0h-i.py` | `m/86'/0'/0'/{i}` | Taproot (P2TR) | BIP86 (2021) |

Usage:

```bash
python derive/m-44h-0h-0h-i.py -n 3 "word1 word2 ... word12"
python derive/m-0h-i.py -n 2 "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
python derive/m-0h-0h-0h.py -n 1 "mnemonic phrase"
```

Also kept (not derivation-path named):
- `derive/all_address_types.py`
- `derive/brain_wallet.py`
- `derive/generate_mnemonic.py`
- `derive/derivation_cli.py`

---

## Tests

- `tests/test_*.py` — 13 test files comparing output to golden fixtures
- `tests/fixtures/*.json` — 12 reference outputs (generate_mnemonic excluded — random)

```bash
pytest tests/
```

---

## Security Best Practices

1. **Never use the bundled test mnemonic** for real funds
2. **Never share or commit** real mnemonics, seeds, private keys, WIFs
3. **Verify derivation paths, address types, and network** match your wallet
4. **Prefer established wallets** with hardware signer support
5. **Test first** — use testnet or small amounts
6. **Keep backups secure** — offline, encrypted
