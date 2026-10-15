# WIP dont' use

### Method 2: Using sweep/sweep.py

```
# NetworkAPI tries the following services in order until one succeeds:Mainnet
# 
# - BlockchairAPI
# - BlockstreamAPI
# - BitcoreAPI (Insight API)
# - SmartbitAPI
# - BlockchainAPI (blockchain.info)

python sweep/sweep.py -h
usage: sweep.py [-h] [--testnet] wif_key dest_address

Programmatically transfer all bitcoin from a private key to a destination address.

positional arguments:
  wif_key       The WIF format private key of the source address
  dest_address  The destination Bitcoin address

options:
  -h, --help    show this help message and exit
  --testnet     Use testnet instead of mainnet

```

### Method 2: Using Bitcoin Core (`bitcoin-cli`) via Bash

If you already run a local Bitcoin Core node, you can safely import the private key into a temporary descriptor wallet, let the node find the UTXOs, and send everything.

#### Step-by-Step Bash Commands:

1. **Create a temporary wallet for the import:**

   Bash

   ```
   bitcoin-cli createwallet "sweep_wallet" true
   ```

2. **Import your private key:**

   Bash

   ```
   bitcoin-cli -rpcwallet="sweep_wallet" importprivkey "YOUR_PRIVATE_KEY_IN_WIF_FORMAT" "my_key" false
   ```

3. **Send all funds to the destination address (substituting fee automatically):**

   Bash

   ```
   bitcoin-cli -rpcwallet="sweep_wallet" sendtoaddress "DESTINATION_BITCOIN_ADDRESS" 0.00000000 "" "" true
   ```

   *(Note: Setting the amount to `0` and passing `true` for `subfeefromamount` tells Bitcoin Core to deduct the transaction fee from the total balance, effectively sweeping everything).*

4. **Unload/Delete the temporary wallet when done:**

   Bash

   ```
   bitcoin-cli unloadwallet "sweep_wallet"
   ```

- **Verification:** Run `bitcoin-cli -rpcwallet="sweep_wallet" getwalletinfo` before unloading, or look up the generated txid via an explorer to verify success.
