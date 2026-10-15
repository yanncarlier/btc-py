# Bitcoin Address Generation API

**Disclaimer: Use at Your Own Risk** This is experimental beta software and may contain bugs or exhibit unexpected behavior. It is provided "as-is" without any warranties. Use of this software is entirely at your own discretion and risk.

A FastAPI-based RESTful API for generating Bitcoin mnemonic seeds and various address types including BIP32, BIP44, BIP49, BIP84, and BIP86.

## Features

- Generate BIP39 mnemonic phrases and seeds
- Create brain wallets from passphrases
- Generate Bitcoin addresses with different derivation schemes:
  - BIP32 (Custom derivation paths)
  - BIP44 (Legacy P2PKH)
  - BIP49 (Wrapped SegWit P2SH-P2WPKH)
  - BIP84 (Native SegWit P2WPKH)
  - BIP86 (Taproot P2TR)
- Rate limiting per IP address
- CORS support
- Detailed API documentation via OpenAPI/Swagger

## Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:yanncarlier/btcapi.git
cd btcapi
```

1. Create a virtual environment:

bash

```bash
python -m venv .venv
source .venv/bin/activate  
```

1. Install dependencies:

bash

```bash
pip install -r requirements.txt
```

Usage

1. Run the development server:

bash

```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000
```

1. Access the API:

- Development server: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Redoc documentation: http://127.0.0.1:8000/redoc

API Endpoints

| Endpoint                  | Method | Description                                |
| ------------------------- | ------ | ------------------------------------------ |
| /                         | GET    | Root endpoint returning a greeting         |
| /generate-mnemonic        | GET    | Generate a new BIP39 mnemonic and seed     |
| /generate-brain-wallet    | POST   | Generate a brain wallet from a passphrase  |
| /generate-bip32-addresses | POST   | Generate BIP32 addresses with custom paths |
| /generate-bip44-addresses | POST   | Generate BIP44 legacy addresses            |
| /generate-bip49-addresses | POST   | Generate BIP49 wrapped SegWit addresses    |
| /generate-bip84-addresses | POST   | Generate BIP84 native SegWit addresses     |
| /generate-bip86-addresses | POST   | Generate BIP86 Taproot addresses           |

Configuration

- MAX_ADDRESSES: Maximum number of addresses per request (default: 10)
- RATE_LIMIT: Maximum requests per IP (default: 60)
- TIME_FRAME: Rate limiting window (default: 1 hour)
- origins: Allowed CORS origins

Security Features

- Rate limiting per IP address
- CORS middleware
- X-Content-Type-Options header
- Input validation
- Optional private key inclusion

Request Examples

Generate Mnemonic

bash

```bash
curl http://127.0.0.1:8000/generate-mnemonic
```

Generate BIP84 Addresses

bash

```bash
curl -X POST http://127.0.0.1:8000/generate-bip84-addresses \
-H "Content-Type: application/json" \
-d '{
    "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
    "passphrase": "",
    "num_addresses": 1,
    "include_private_keys": false
}'
```

Response Format

Successful responses return JSON with address details:

json

```json
{
    "addresses": [
        {
            "derivation_path": "m/84'/0'/0'/0/0",
            "address": "bc1q...",
            "public_key": "02...",
            "extended_private_key": null,
            "private_key": null,
            "wif": null
        }
    ]
}
```

Dependencies

- fastapi
- pydantic
- ecdsa
- base58
- bip-utils
- bip32utils
- mnemonic
- uvicorn

Development

To contribute:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

License

MIT License (LICENSE)

Disclaimer

This software is for educational purposes only. Use at your own risk, especially when handling real cryptocurrency funds. Always verify generated addresses and keep private keys secure.

```text
To use this README:

1. Create a `README.md` file in your project root
2. Copy and paste the content above
3. Customize as needed:
   - Update the repository URL
   - Add specific license information
   - Modify installation instructions if different
   - Add any additional sections specific to your deployment

You might also want to create a `requirements.txt` file with:
```

fastapi pydantic ecdsa base58 bip-utils bip32utils mnemonic uvicorn