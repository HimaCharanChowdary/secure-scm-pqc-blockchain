import os
import json
import hashlib
import time
import random
from datetime import datetime, timedelta
from web3 import Web3
from dilithium_py.dilithium import Dilithium2
from generate_keys import load_keys

# CONFIGURATION
DATASET_PATH       = "sample_dataset"
SIGNATURES_FILE    = "contract_signatures.json"
TRANSACTIONS_FILE  = "transactions.json"

ORGS         = ["Auditor_Org", "Deployer_Org", "Verifier_Org", "Monitor_Org"]
NORMAL_ROUTE = ["Auditor_Org", "Deployer_Org", "Verifier_Org"]

# CONNECT TO GANACHE
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

registry = w3.eth.contract(
    address=registry_info["address"],
    abi=json.loads(registry_info["abi"])
)
account = w3.eth.accounts[0]

# PROGRESS BAR
def print_progress(current, total, start_time, bar_length=38):
    percent  = current / total
    filled   = int(bar_length * percent)
    bar      = "█" * filled + "░" * (bar_length - filled)
    elapsed  = time.time() - start_time
    if current > 0:
        eta        = (elapsed / current) * (total - current)
        mins, secs = divmod(int(eta), 60)
        eta_str    = f"{mins}m {secs}s left"
    else:
        eta_str = "calculating..."
    print(f"\r  [{bar}] {current}/{total} ({percent*100:.1f}%)  ⏳ {eta_str}",
          end="", flush=True)


# LOAD APPROVED CONTRACTS
def load_approved_contracts():
    print("\n📂 Scanning dataset for approved contracts...")

    sol_files = []
    for root, dirs, files in os.walk(DATASET_PATH):
        for file in files:
            if file.endswith(".sol"):
                sol_files.append(os.path.join(root, file))

    try:
        with open(SIGNATURES_FILE, "r") as f:
            signatures = json.load(f)
    except FileNotFoundError:
        signatures = {}

    approved = []
    for path in sol_files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            contract_hash = hashlib.sha256(source.encode()).digest()
            hash_hex      = contract_hash.hex()
            if hash_hex in signatures:
                approved.append({
                    "path"         : path,
                    "source"       : source,
                    "contract_hash": hash_hex,
                    "signature"    : signatures[hash_hex]["signature"],
                    "public_key"   : signatures[hash_hex]["public_key"],
                    "loc"          : len(source.splitlines()),
                    "size_bytes"   : len(source.encode())
                })
        except Exception:
            continue

    print(f"   ✅ Approved contracts loaded: {len(approved)}\n")
    return approved


# GENERATE TRANSACTION
def generate_transaction(contract, tx_index, sk, pk, base_time,
                          is_anomaly, anomaly_type, all_hashes):

    loc           = contract["loc"]
    size_bytes    = contract["size_bytes"]
    route         = NORMAL_ROUTE.copy()
    time_gap      = timedelta(minutes=random.randint(30, 120))
    contract_hash = contract["contract_hash"]
    hash_freq     = 1

    if anomaly_type == "unusual_route":
        # Completely bypass Deployer and Verifier
        route = ["Auditor_Org", "Monitor_Org"]

    elif anomaly_type == "duplicate_submission":
        # Pick a hash that appears multiple times
        # Force hash_freq = 5 by picking a repeated hash
        contract_hash = random.choice(all_hashes)
        hash_freq     = 5   # explicitly mark as repeated

    elif anomaly_type == "abnormal_size":
        # 15x to 25x larger — well outside normal range
        multiplier = random.uniform(15.0, 25.0)
        loc        = int(loc * multiplier)
        size_bytes = int(size_bytes * multiplier)

    elif anomaly_type == "rapid_resubmission":
        # 1 to 3 seconds — extreme outlier
        time_gap = timedelta(seconds=random.randint(1, 3))

    tx_time = base_time + time_gap

    payload = {
        "shipmentId"  : f"SHP{tx_index:05d}",
        "contractHash": contract_hash,
        "fromOrg"     : route[0],
        "toOrg"       : route[-1],
        "route"       : route,
        "status"      : "APPROVED",
        "loc"         : loc,
        "sizeBytes"   : size_bytes,
        "hashFreq"    : hash_freq,
        "timestamp"   : tx_time.isoformat(),
        "isAnomaly"   : is_anomaly,
        "anomalyType" : anomaly_type
    }

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_hash  = hashlib.sha256(payload_bytes).digest()
    tx_signature  = Dilithium2.sign(sk, payload_hash)

    try:
        tx_hash = registry.functions.approveContract(payload_hash).transact({
            "from": account
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        on_chain = True
    except Exception:
        on_chain = False

    return {
        **payload,
        "payloadHash"       : payload_hash.hex(),
        "txSignature"       : tx_signature.hex(),
        "txPublicKey"       : pk.hex(),
        "contractSignature" : contract["signature"],
        "onChain"           : on_chain
    }, tx_time


# MAIN
def main():
    print("\n" + "=" * 60)
    print("  Supply Chain Simulator — Smart Contract Shipments")
    print("=" * 60)

    print("\n🔑 Loading Dilithium keys...")
    try:
        pk, sk = load_keys()
        print("✅ Keys loaded\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    approved = load_approved_contracts()
    if not approved:
        print("❌ No approved contracts found.")
        return

    # All contract hashes for duplicate injection
    all_hashes = [c["contract_hash"] for c in approved]

    # Assign labels
    n_total   = len(approved)
    n_anomaly = int(n_total * 0.08)
    n_normal  = n_total - n_anomaly

    anomaly_types = ["unusual_route", "duplicate_submission",
                     "abnormal_size", "rapid_resubmission"]

    labels = (
        [(False, None)] * n_normal +
        [(True, anomaly_types[i % 4]) for i in range(n_anomaly)]
    )
    random.shuffle(labels)

    print(f"🚚 Generating {n_total} transactions ({n_anomaly} anomalies)...\n")

    transactions = []
    base_time    = datetime(2025, 1, 1, 9, 0, 0)
    start_time   = time.time()

    for i, (contract, (is_anomaly, anomaly_type)) in enumerate(zip(approved, labels)):
        tx, base_time = generate_transaction(
            contract, i + 1, sk, pk, base_time,
            is_anomaly, anomaly_type, all_hashes
        )
        transactions.append(tx)
        print_progress(i + 1, n_total, start_time)

    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=2)

    elapsed      = time.time() - start_time
    mins, secs   = divmod(int(elapsed), 60)
    anomaly_count = sum(1 for tx in transactions if tx["isAnomaly"])

    print(f"\n\n{'='*60}")
    print("  Simulation Complete")
    print(f"{'='*60}")
    print(f"  Total transactions  : {len(transactions)}")
    print(f"  Normal              : {len(transactions) - anomaly_count}")
    print(f"  Anomalies injected  : {anomaly_count} ({anomaly_count/len(transactions)*100:.1f}%)")
    print(f"  Saved to            : {TRANSACTIONS_FILE}")
    print(f"  Time taken          : {mins}m {secs}s")
    print(f"{'='*60}\n")

    print("📊 Anomaly Breakdown:")
    counts = {}
    for tx in transactions:
        if tx["isAnomaly"]:
            t = tx["anomalyType"]
            counts[t] = counts.get(t, 0) + 1
    for atype, count in sorted(counts.items()):
        print(f"   {atype:<30}: {count}")
    print()


if __name__ == "__main__":
    main()