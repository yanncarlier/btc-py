# btc-py

Bitcoin tooling: a FastAPI service and a set of educational CLI scripts for
mnemonic generation, address derivation, and address balance lookups.

## Layout

```
api/       FastAPI service (v2.0.0)
scripts/
  derive/     key and address derivation
  explorers/  address balance lookups via public APIs
  sweep/      WIP - sweep a full balance to an address
  tests/
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Install

Each directory is an independent environment.

```bash
# API
cd api
uv venv && source .venv/bin/activate
uv pip install -r requirements.in

# Scripts
cd scripts
uv venv && source .venv/bin/activate
uv sync
uv pip install -r requirements.txt
```

`uv sync` alone is not enough for `scripts`: `pyproject.toml` lists only `bit`
and `bip-utils`, while the scripts also need `mnemonic`, `base58`, `bip32utils`
and `bitcoinlib` from `requirements.in`.

## Run

### API

```bash
cd api && source .venv/bin/activate
python main.py                      # or: uvicorn main:app --port 8000
```

- <http://127.0.0.1:8000/docs> — Swagger UI
- <http://127.0.0.1:8000/redoc> — ReDoc

| Endpoint | Method |
| --- | --- |
| `/generate-mnemonic` | GET |
| `/generate-brain-wallet` | POST |
| `/generate-bip32-addresses` | POST |
| `/generate-bip44-addresses` | POST |
| `/generate-bip49-addresses` | POST |
| `/generate-bip84-addresses` | POST |
| `/generate-bip86-addresses` | POST |

```bash
curl -X POST http://127.0.0.1:8000/generate-bip84-addresses \
  -H "Content-Type: application/json" \
  -d '{"mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about", "num_addresses": 1}'
```

### Scripts

```bash
cd scripts && source .venv/bin/activate

python derive/generate_mnemonic.py -s 128
python derive/m-44h-0h-0h-i.py -n 1 "word1 word2 ... word12"
python explorers/mempool.space.py bc1qexampleaddress
```

Derivation scripts are named after their BIP32 path, where `/` becomes `-` and
`'` becomes `h` — so `m-84h-0h-0h-i.py` is `m/84'/0'/0'/0/n`.

## Tests

```bash
cd scripts && .venv/bin/python -m pytest tests/
```

Tests invoke each script as a subprocess and compare the output against the
golden fixtures in `tests/fixtures/`, so they must be run from `scripts/`.

## Security

Never use the bundled test mnemonic for real funds, and never commit real
mnemonics, seeds or private keys. See [SECURITY.md](SECURITY.md).

## Disclaimer

Educational software, provided as-is with no warranties. Use at your own risk.