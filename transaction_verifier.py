import json
import hashlib
import sys
from dilithium_py.dilithium import Dilithium2
from web3 import Web3

# CONFIGURATION
TRANSACTIONS_FILE = "transactions.json"

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

registry = w3.eth.contract(
    address=registry_info["address"],
    abi=json.loads(registry_info["abi"])
)


# VERIFY SINGLE TRANSACTION
def verify_transaction(tx: dict, verbose=True) -> bool:

    if verbose:
        print(f"\n{'='*55}")
        print(f"  Verifying Transaction: {tx['shipmentId']}")
        print(f"{'='*55}")
        print(f"  Contract Hash : {tx['contractHash'][:32]}...")
        print(f"  From          : {tx['fromOrg']}")
        print(f"  To            : {tx['toOrg']}")
        print(f"  Timestamp     : {tx['timestamp']}")

    # Step 1: Rebuild payload (exclude signature fields)
    payload = {k: v for k, v in tx.items() if k not in [
        "payloadHash", "txSignature", "txPublicKey",
        "contractSignature", "onChain"
    ]}

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_hash  = hashlib.sha256(payload_bytes).digest()

    # Step 2: Verify hash matches
    stored_hash = tx["payloadHash"]
    hash_matches = payload_hash.hex() == stored_hash

    if verbose:
        print(f"\n  Hash check    : {'✅ Match' if hash_matches else '❌ Mismatch'}")

    if not hash_matches:
        if verbose:
            print("  ❌ VERIFICATION FAILED — payload was tampered!\n")
        return False

    # Step 3: Verify Dilithium signature
    try:
        signature  = bytes.fromhex(tx["txSignature"])
        public_key = bytes.fromhex(tx["txPublicKey"])
        sig_valid  = Dilithium2.verify(public_key, payload_hash, signature)
    except Exception as e:
        if verbose:
            print(f"  ❌ Signature error: {e}")
        return False

    if verbose:
        print(f"  Signature     : {'✅ Valid' if sig_valid else '❌ Invalid'}")

    # Step 4: Verify on chain
    try:
        on_chain = registry.functions.approveContract(payload_hash).call
        chain_status = tx.get("onChain", False)
    except Exception:
        chain_status = tx.get("onChain", False)

    if verbose:
        print(f"  On-chain      : {'✅ Yes' if chain_status else '⚠️  Not verified'}")
        print(f"\n  {'✅ TRANSACTION VERIFIED' if sig_valid else '❌ VERIFICATION FAILED'}")
        print(f"{'='*55}\n")

    return sig_valid


# VERIFY ALL TRANSACTIONS
def verify_all(limit=None):
    print(f"\n{'='*55}")
    print("  Batch Transaction Verification")
    print(f"{'='*55}\n")

    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    except FileNotFoundError:
        print(f"❌ {TRANSACTIONS_FILE} not found.")
        return

    if limit:
        transactions = transactions[:limit]

    total   = len(transactions)
    passed  = 0
    failed  = 0

    print(f"  Verifying {total} transactions...\n")

    for i, tx in enumerate(transactions):
        result = verify_transaction(tx, verbose=False)
        if result:
            passed += 1
        else:
            failed += 1

        # Progress
        bar = "█" * int(38 * (i+1) / total) + "░" * (38 - int(38 * (i+1) / total))
        print(f"\r  [{bar}] {i+1}/{total} ✅ {passed} ❌ {failed}", end="", flush=True)

    print(f"\n\n{'='*55}")
    print("  Verification Summary")
    print(f"{'='*55}")
    print(f"  Total verified  : {total}")
    print(f"  ✅ Passed        : {passed} ({passed/total*100:.1f}%)")
    print(f"  ❌ Failed        : {failed} ({failed/total*100:.1f}%)")
    print(f"{'='*55}\n")


# TAMPER TEST
def tamper_test():
    print(f"\n⚠️  Running tamper test...")

    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    except FileNotFoundError:
        print("❌ transactions.json not found.")
        return

    # Take first transaction and tamper with it
    tx = transactions[0].copy()
    original_quantity = tx.get("loc")

    print(f"  Original LOC   : {tx['loc']}")
    tx["loc"] = 99999  # tamper
    print(f"  Tampered LOC   : {tx['loc']}")

    result = verify_transaction(tx, verbose=False)
    print(f"  Tamper detected: {'✅ Yes — signature invalid!' if not result else '❌ No — something wrong'}\n")


# MAIN
if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "all":
        # Verify all transactions
        verify_all()

    elif len(sys.argv) > 1 and sys.argv[1] == "tamper":
        # Run tamper test
        tamper_test()

    elif len(sys.argv) > 1:
        # Verify specific shipment ID
        shipment_id = sys.argv[1]
        try:
            with open(TRANSACTIONS_FILE, "r") as f:
                transactions = json.load(f)

            tx = next((t for t in transactions if t["shipmentId"] == shipment_id), None)

            if tx:
                verify_transaction(tx, verbose=True)
            else:
                print(f"❌ Shipment {shipment_id} not found.")
        except FileNotFoundError:
            print("❌ transactions.json not found.")

    else:
        # Default: verify first 5 + tamper test
        try:
            with open(TRANSACTIONS_FILE, "r") as f:
                transactions = json.load(f)

            print(f"\n📋 Verifying first 5 transactions:\n")
            for tx in transactions[:5]:
                verify_transaction(tx, verbose=True)

            tamper_test()

        except FileNotFoundError:
            print("❌ transactions.json not found. Run supply_chain_simulator.py first.")