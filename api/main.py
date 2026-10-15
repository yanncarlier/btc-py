# Standard Library Imports
from typing import Optional
import hashlib
import hmac
import threading
from datetime import datetime, timedelta

# Third-Party Imports
from fastapi import FastAPI, HTTPException, Body, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base58
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from mnemonic import Mnemonic

# Constants
MAX_ADDRESSES = 10
RATE_LIMIT = 60
TIME_FRAME = timedelta(hours=1)
BIP32_HARDEN = 0x80000000  # Hardened index offset
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# In-memory storage for rate limiting
request_timestamps = {}
rate_limit_lock = threading.Lock()

# FastAPI Application Setup
app = FastAPI(
    title="Bitcoin Address Generation API",
    version="1.0.0",
    description="API for generating Bitcoin mnemonic seeds and various address types (BIP32, BIP44, BIP49, BIP84, BIP86).",
    servers=[
        # {"url": "http://0.0.0.0:8000/", "description": "Development server"},
        {"url": "https://btcapi.bitcoin-tx.com", "description": "Production environment"}
    ]
)

origins = [
    "https://btcapi.bitcoin-tx.com",
    "https://www.bitcoin-tx.com",
    "https://bitcoin-tx.com",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_x_content_type_options_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not client_ip:
        raise HTTPException(status_code=400, detail="Client IP not found")
    
    current_time = datetime.now()
    window_start = current_time - TIME_FRAME
    
    with rate_limit_lock:
        if client_ip in request_timestamps:
            request_timestamps[client_ip] = [ts for ts in request_timestamps[client_ip] if ts > window_start]
            if not request_timestamps[client_ip]:
                del request_timestamps[client_ip]
        
        if len(request_timestamps.get(client_ip, [])) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = "0"
            if request_timestamps.get(client_ip):
                oldest_ts = request_timestamps[client_ip][0]
                retry_after = (oldest_ts + TIME_FRAME - current_time).total_seconds()
                response.headers["Retry-After"] = str(int(retry_after))
            return response
        
        remaining = max(0, RATE_LIMIT - (len(request_timestamps.get(client_ip, [])) + 1))
    
    response = await call_next(request)
    
    with rate_limit_lock:
        if client_ip not in request_timestamps:
            request_timestamps[client_ip] = []
        request_timestamps[client_ip].append(current_time)
    
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# Pydantic Models
class MnemonicResponse(BaseModel):
    BIP39Mnemonic: str
    BIP39Seed: str
    BIP32RootKey: str

class AddressRequest(BaseModel):
    mnemonic: str
    passphrase: Optional[str] = ""
    num_addresses: Optional[int] = 1
    include_private_keys: bool = False
    derivation_path: Optional[str] = "m/0/{index}"

class AddressDetails(BaseModel):
    derivation_path: str
    address: str
    public_key: str
    private_key: Optional[str] = None
    wif: Optional[str] = None

class Bip32AddressListResponse(BaseModel):
    account_xpub: str
    bip32_xpub: str
    addresses: list[AddressDetails]

class BrainWalletRequest(BaseModel):
    passphrase: str
    include_private_keys: bool = False

class BrainWalletResponse(BaseModel):
    bitcoin_address: str
    public_key: str
    wif_private_key: Optional[str] = None

# Bech32 Encoding for BIP84 and BIP86
def bech32_encode(hrp: str, data: bytes) -> str:
    """Encode data in Bech32 format for Bitcoin addresses (BIP84, BIP86)."""
    def convertbits(data: bytes, frombits: int, tobits: int, pad: bool = True) -> list[int]:
        acc = 0
        bits = 0
        ret = []
        maxv = (1 << tobits) - 1
        for value in data:
            acc = (acc << 8) | value
            bits += 8
            while bits >= tobits:
                bits -= tobits
                ret.append((acc >> bits) & maxv)
        if pad and bits:
            ret.append((acc << (tobits - bits)) & maxv)
        return ret

    def create_checksum(hrp: str, data: list[int]) -> list[int]:
        values = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + data
        poly = 1
        for v in values:
            poly ^= v
            for _ in range(5):
                poly = (poly >> 1) ^ (0x3b6a57b2 if poly & 1 else 0)
        return [(poly >> (5 * (5 - i))) & 31 for i in range(6)]

    charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    witver = 0  # Witness version 0 for P2WPKH, 1 for P2TR
    if hrp == "bc" and data[0] == 0x51:  # P2TR (BIP86)
        witver = 1
        data = data[2:]  # Remove script prefix \x51\x20
    data5 = convertbits(data, 8, 5)
    checksum = create_checksum(hrp, [witver] + data5)
    return hrp + "1" + "".join(charset[d] for d in ([witver] + data5 + checksum))

# BIP32 Implementation
def _bip32_derive(seed: bytes, path: str) -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    """Derive a BIP32 private key and chain code from a seed and derivation path."""
    def _ckd_priv(k: bytes, c: bytes, index: int) -> tuple[bytes, bytes]:
        is_hardened = index >= BIP32_HARDEN
        index = index % BIP32_HARDEN if is_hardened else index
        if is_hardened:
            data = b'\x00' + k + index.to_bytes(4, 'big')
        else:
            private_key = ec.derive_private_key(int.from_bytes(k, 'big'), ec.SECP256K1())
            pubkey = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.CompressedPoint
            )
            data = pubkey + index.to_bytes(4, 'big')
        hmac_obj = hmac.new(c, data, hashlib.sha512)
        hmac_data = hmac_obj.digest()
        Il, Ir = hmac_data[:32], hmac_data[32:]
        child_k = (int.from_bytes(Il, 'big') + int.from_bytes(k, 'big')) % SECP256K1_ORDER
        if child_k == 0:
            raise ValueError("Invalid child key (zero)")
        return child_k.to_bytes(32, 'big'), Ir

    hmac_obj = hmac.new(b"Bitcoin seed", seed, hashlib.sha512)
    master_key = hmac_obj.digest()
    k, c = master_key[:32], master_key[32:]

    parts = path.split('/')[1:]  # Skip 'm'
    for part in parts:
        if part.endswith("'"):
            index = int(part[:-1]) + BIP32_HARDEN
        else:
            index = int(part)
        k, c = _ckd_priv(k, c, index)

    private_key = ec.derive_private_key(int.from_bytes(k, 'big'), ec.SECP256K1())
    return private_key, c

def _bip32_xpub(private_key: ec.EllipticCurvePrivateKey, chain_code: bytes) -> str:
    """Generate extended public key (xpub) in Base58 format."""
    pubkey = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )
    version = b'\x04\x88\xB2\x1E'  # xpub prefix for Bitcoin mainnet
    depth = b'\x00'  # Simplified for master or account level
    fingerprint = b'\x00\x00\x00\x00'  # Parent fingerprint (0 for simplicity)
    child_number = b'\x00\x00\x00\x00'  # Child number (0 for simplicity)
    data = version + depth + fingerprint + child_number + chain_code + pubkey
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return base58.b58encode(data + checksum).decode('utf-8')

def _generate_address(private_key: ec.EllipticCurvePrivateKey, addr_type: str) -> tuple[str, str, str]:
    """Generate Bitcoin address, public key, and WIF private key for given address type."""
    pubkey = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pubkey_compressed = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )

    # Generate private key WIF
    privkey_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    wif_data = b'\x80' + privkey_bytes
    wif_checksum = hashlib.sha256(hashlib.sha256(wif_data).digest()).digest()[:4]
    wif = base58.b58encode(wif_data + wif_checksum).decode('utf-8')

    # Generate address based on type
    if addr_type == "P2PKH":  # BIP44
        hash1 = hashlib.sha256(pubkey).digest()
        hash2 = hashlib.new('ripemd160')
        hash2.update(hash1)
        pubkey_hash = hash2.digest()
        addr_data = b'\x00' + pubkey_hash
        checksum = hashlib.sha256(hashlib.sha256(addr_data).digest()).digest()[:4]
        addr = base58.b58encode(addr_data + checksum).decode('utf-8')
    elif addr_type == "P2SH-P2WPKH":  # BIP49
        hash1 = hashlib.sha256(pubkey_compressed).digest()
        hash2 = hashlib.new('ripemd160')
        hash2.update(hash1)
        witness_program = hash2.digest()
        script = b'\x00\x14' + witness_program
        hash3 = hashlib.sha256(script).digest()
        hash4 = hashlib.new('ripemd160')
        hash4.update(hash3)
        addr_data = b'\x05' + hash4.digest()
        checksum = hashlib.sha256(hashlib.sha256(addr_data).digest()).digest()[:4]
        addr = base58.b58encode(addr_data + checksum).decode('utf-8')
    elif addr_type == "P2WPKH":  # BIP84
        hash1 = hashlib.sha256(pubkey_compressed).digest()
        hash2 = hashlib.new('ripemd160')
        hash2.update(hash1)
        addr_data = hash2.digest()
        addr = bech32_encode("bc", b'\x00' + addr_data)
    elif addr_type == "P2TR":  # BIP86
        addr_data = pubkey_compressed[1:]  # Remove 0x02/0x03 prefix
        addr = bech32_encode("bc", b'\x51\x20' + addr_data)
    else:
        raise ValueError(f"Unsupported address type: {addr_type}")

    return wif, addr, pubkey_compressed.hex()

# Helper Functions
def generate_brain_wallet(passphrase: str) -> tuple[str, str, str]:
    private_key_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        passphrase.encode('utf-8'),
        b'brain-wallet',
        200_000,
        dklen=32,
    )
    private_key = ec.derive_private_key(int.from_bytes(private_key_bytes, 'big'), ec.SECP256K1())
    return _generate_address(private_key, "P2PKH")

async def _generate_bip32_addresses(request: AddressRequest) -> dict:
    try:
        if request.num_addresses < 1 or request.num_addresses > MAX_ADDRESSES:
            raise ValueError(f"Number of addresses must be between 1 and {MAX_ADDRESSES}")

        mnemo = Mnemonic("english")
        if not mnemo.check(request.mnemonic):
            raise ValueError("Invalid mnemonic phrase.")
        seed = mnemo.to_seed(request.mnemonic, passphrase=request.passphrase)

        parts = request.derivation_path.split('/')
        if parts[-1] != '{index}':
            raise ValueError("Derivation path must end with '/{index}'")
        account_parts = parts[:-2] if len(parts) > 2 else parts[:-1]
        account_path = '/'.join(['m'] + account_parts)
        account_key, account_chain_code = _bip32_derive(seed, account_path)
        account_xpub = _bip32_xpub(account_key, account_chain_code)

        base_path = '/'.join(parts[:-1])
        base_key, base_chain_code = _bip32_derive(seed, base_path)
        bip32_xpub = _bip32_xpub(base_key, base_chain_code)

        addresses = []
        for i in range(request.num_addresses):
            derivation_path = request.derivation_path.replace("{index}", str(i))
            private_key, _ = _bip32_derive(seed, derivation_path)
            wif, address, public_key = _generate_address(private_key, "P2PKH")
            addresses.append({
                "derivation_path": derivation_path,
                "address": address,
                "public_key": public_key,
                "private_key": private_key.private_numbers().private_value.to_bytes(32, 'big').hex() if request.include_private_keys else None,
                "wif": wif if request.include_private_keys else None
            })

        return {
            "account_xpub": account_xpub,
            "bip32_xpub": bip32_xpub,
            "addresses": addresses
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _generate_bip_addresses(request: AddressRequest, purpose: int, addr_type: str) -> dict:
    try:
        if request.num_addresses < 1 or request.num_addresses > MAX_ADDRESSES:
            raise ValueError(f"Number of addresses must be between 1 and {MAX_ADDRESSES}")

        mnemo = Mnemonic("english")
        if not mnemo.check(request.mnemonic):
            raise ValueError("Invalid mnemonic phrase.")
        seed = mnemo.to_seed(request.mnemonic, passphrase=request.passphrase)

        account_path = f"m/{purpose}'/0'/0'"
        account_key, account_chain_code = _bip32_derive(seed, account_path)
        account_xpub = _bip32_xpub(account_key, account_chain_code)

        base_path = f"m/{purpose}'/0'/0'/0"
        base_key, base_chain_code = _bip32_derive(seed, base_path)
        bip32_xpub = _bip32_xpub(base_key, base_chain_code)

        addresses = []
        for i in range(request.num_addresses):
            derivation_path = f"m/{purpose}'/0'/0'/0/{i}"
            private_key, _ = _bip32_derive(seed, derivation_path)
            wif, address, public_key = _generate_address(private_key, addr_type)
            addresses.append({
                "derivation_path": derivation_path,
                "address": address,
                "public_key": public_key,
                "private_key": private_key.private_numbers().private_value.to_bytes(32, 'big').hex() if request.include_private_keys else None,
                "wif": wif if request.include_private_keys else None
            })

        return {
            "account_xpub": account_xpub,
            "bip32_xpub": bip32_xpub,
            "addresses": addresses
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API Endpoints
@app.get(
    "/",
    summary="Root Endpoint",
    description="Returns a simple greeting message."
)
async def read_root():
    return {"Hello": "World"}

@app.get(
    "/generate-mnemonic",
    response_model=MnemonicResponse,
    summary="Generate BIP39 Mnemonic",
    description="Generates a new BIP39 mnemonic phrase and its corresponding seed."
)
async def generate_mnemonic():
    mnemo = Mnemonic("english")
    words = mnemo.generate(128)
    seed = mnemo.to_seed(words)
    private_key, chain_code = _bip32_derive(seed, "m")
    bip32_root_key = _bip32_xpub(private_key, chain_code)
    return {
        "BIP39Mnemonic": words,
        "BIP39Seed": seed.hex(),
        "BIP32RootKey": bip32_root_key
    }

@app.post(
    "/generate-brain-wallet",
    response_model=BrainWalletResponse,
    summary="Generate Brain Wallet",
    description="Generates a Bitcoin address and keys from a passphrase."
)
async def generate_brain_wallet_endpoint(request: BrainWalletRequest = Body(...)):
    try:
        wif, addr, pub_key = generate_brain_wallet(request.passphrase)
        return {
            "bitcoin_address": addr,
            "public_key": pub_key,
            "wif_private_key": wif if request.include_private_keys else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post(
    "/generate-bip32-addresses",
    response_model=Bip32AddressListResponse,
    summary="Generate BIP32 Addresses (custom derivation paths)",
    description="Generates BIP32 legacy Bitcoin addresses from a mnemonic phrase with custom derivation paths."
)
async def generate_bip32_addresses(request: AddressRequest = Body(
    ...,
    example={
        "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        "passphrase": "",
        "num_addresses": 1,
        "include_private_keys": False,
        "derivation_path": "m/0'/0/{index}"
    }
)):
    result = await _generate_bip32_addresses(request)
    return Bip32AddressListResponse(
        account_xpub=result["account_xpub"],
        bip32_xpub=result["bip32_xpub"],
        addresses=[AddressDetails(**addr) for addr in result["addresses"]]
    )

@app.post(
    "/generate-bip44-addresses",
    response_model=Bip32AddressListResponse,
    summary="Generate BIP44 Addresses",
    description="Generates BIP44 legacy Bitcoin addresses (P2PKH) from a mnemonic phrase."
)
async def generate_bip44_addresses(
    request: AddressRequest = Body(
        ...,
        example={
            "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "passphrase": "",
            "num_addresses": 1,
            "include_private_keys": False
        }
    )
):
    result = await _generate_bip_addresses(request, 44, "P2PKH")
    return Bip32AddressListResponse(
        account_xpub=result["account_xpub"],
        bip32_xpub=result["bip32_xpub"],
        addresses=[AddressDetails(**addr) for addr in result["addresses"]]
    )

@app.post(
    "/generate-bip49-addresses",
    response_model=Bip32AddressListResponse,
    summary="Generate BIP49 Addresses",
    description="Generates BIP49 Wrapped SegWit (P2SH-P2WPKH) Bitcoin addresses from a mnemonic phrase."
)
async def generate_bip49_addresses(
    request: AddressRequest = Body(
        ...,
        example={
            "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "passphrase": "",
            "num_addresses": 1,
            "include_private_keys": False
        }
    )
):
    result = await _generate_bip_addresses(request, 49, "P2SH-P2WPKH")
    return Bip32AddressListResponse(
        account_xpub=result["account_xpub"],
        bip32_xpub=result["bip32_xpub"],
        addresses=[AddressDetails(**addr) for addr in result["addresses"]]
    )

@app.post(
    "/generate-bip84-addresses",
    response_model=Bip32AddressListResponse,
    summary="Generate BIP84 Addresses",
    description="Generates BIP84 Native SegWit (P2WPKH) Bitcoin addresses from a mnemonic phrase."
)
async def generate_bip84_addresses(
    request: AddressRequest = Body(
        ...,
        example={
            "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "passphrase": "",
            "num_addresses": 1,
            "include_private_keys": False
        }
    )
):
    result = await _generate_bip_addresses(request, 84, "P2WPKH")
    return Bip32AddressListResponse(
        account_xpub=result["account_xpub"],
        bip32_xpub=result["bip32_xpub"],
        addresses=[AddressDetails(**addr) for addr in result["addresses"]]
    )

@app.post(
    "/generate-bip86-addresses",
    response_model=Bip32AddressListResponse,
    summary="Generate BIP86 Addresses",
    description="Generates BIP86 Taproot (P2TR) Bitcoin addresses from a mnemonic phrase."
)
async def generate_bip86_addresses(
    request: AddressRequest = Body(
        ...,
        example={
            "mnemonic": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "passphrase": "",
            "num_addresses": 1,
            "include_private_keys": False
        }
    )
):
    result = await _generate_bip_addresses(request, 86, "P2TR")
    return Bip32AddressListResponse(
        account_xpub=result["account_xpub"],
        bip32_xpub=result["bip32_xpub"],
        addresses=[AddressDetails(**addr) for addr in result["addresses"]]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)