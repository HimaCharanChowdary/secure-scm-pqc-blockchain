import os
import hashlib
import json
import time
from web3 import Web3
from dilithium_py.dilithium import Dilithium2
from generate_keys import load_keys

# CONFIGURATION
DATASET_PATH    = "sample_dataset"
SIGNATURES_FILE = "contract_signatures.json"

# CONNECT TO GANACHE
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

registry = w3.eth.contract(
    address=registry_info["address"],
    abi=json.loads(registry_info["abi"])
)

# PROGRESS BAR
def print_progress(current, total, start_time, signed, skipped, bar_length=38):
    percent = current / total
    filled = int(bar_length * percent)
    bar = "█" * filled + "░" * (bar_length - filled)

    elapsed = time.time() - start_time
    if current > 0:
        eta = (elapsed / current) * (total - current)
        mins, secs = divmod(int(eta), 60)
        eta_str = f"{mins}m {secs}s left"
    else:
        eta_str = "calculating..."

    print(
        f"\r  [{bar}] {current}/{total} ({percent*100:.1f}%)"
        f"  ✅ {signed}  ⏭️  {skipped}  ⏳ {eta_str}",
        end="",
        flush=True
    )


# LOAD SIGNATURES FILE
def load_signatures():
    try:
        with open(SIGNATURES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# SAVE SIGNATURES FILE
def save_signatures(data):
    with open(SIGNATURES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# MAIN
def main():
    print("\n" + "=" * 55)
    print("  Sign Approved Contracts with Dilithium2")
    print("=" * 55)

    # Load keys
    print("\n🔑 Loading Dilithium keys...")
    try:
        pk, sk = load_keys()
        print(f"✅ Keys loaded | PK: {pk.hex()[:16]}...\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    # Load existing signatures (resume support)
    signatures = load_signatures()
    already_signed = len(signatures)
    if already_signed > 0:
        print(f"📋 Found {already_signed} existing signatures — will skip those.\n")

    # Collect all contracts
    sol_files = []
    for root, dirs, files in os.walk(DATASET_PATH):
        for file in files:
            if file.endswith(".sol"):
                sol_files.append(os.path.join(root, file))

    print(f"📂 Total contracts in dataset : {len(sol_files)}")
    print(f"🔗 Checking against blockchain...\n")

    # Pre-filter: only approved ones
    approved_contracts = []
    for contract_path in sol_files:
        try:
            with open(contract_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()

            contract_hash = hashlib.sha256(source_code.encode()).digest()
            is_approved = registry.functions.isApproved(contract_hash).call()

            if is_approved:
                approved_contracts.append((contract_path, source_code, contract_hash))

        except Exception:
            continue

    print(f"✅ Approved contracts found    : {len(approved_contracts)}")
    print(f"✍️  Starting Dilithium signing...\n")

    # Sign each approved contract
    signed_count  = 0
    skipped_count = 0
    start_time    = time.time()

    for i, (contract_path, source_code, contract_hash) in enumerate(approved_contracts):
        hash_hex = contract_hash.hex()

        # Skip if already signed
        if hash_hex in signatures:
            skipped_count += 1
            print_progress(i + 1, len(approved_contracts), start_time, signed_count, skipped_count)
            continue

        try:
            # Sign with Dilithium
            signature = Dilithium2.sign(sk, contract_hash)

            # Store in signatures dict
            signatures[hash_hex] = {
                "signature" : signature.hex(),
                "public_key": pk.hex()
            }

            signed_count += 1

            # Save every 100 signatures (safety checkpoint)
            if signed_count % 100 == 0:
                save_signatures(signatures)

        except Exception as e:
            skipped_count += 1

        print_progress(i + 1, len(approved_contracts), start_time, signed_count, skipped_count)

    # Final save
    save_signatures(signatures)

    elapsed = time.time() - start_time
    mins, secs = divmod(int(elapsed), 60)

    print(f"\n\n{'='*55}")
    print("  Signing Complete")
    print(f"{'='*55}")
    print(f"  Total approved contracts : {len(approved_contracts)}")
    print(f"  Newly signed             : {signed_count}")
    print(f"  Already signed (skipped) : {skipped_count}")
    print(f"  Saved to                 : {SIGNATURES_FILE}")
    print(f"  Time taken               : {mins}m {secs}s")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()