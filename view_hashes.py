from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

print("Using contract:", registry_info["address"])

contract = w3.eth.contract(
    address=registry_info["address"],
    abi=json.loads(registry_info["abi"])
)

# ==============================
# METHOD 1: Using event filter (recommended)
# ==============================
print("\n📦 Stored Contract Hashes:\n")

try:
    latest_block = w3.eth.block_number
    print(f"Latest block: {latest_block}")

    # Use the event directly
    event_filter = contract.events.ContractApproved.create_filter(
        fromBlock=0,
        toBlock="latest"
    )

    events = event_filter.get_all_entries()
    print(f"Total contracts stored: {len(events)}\n")

    for i, event in enumerate(events, 1):
        print(f"[{i}] Hash   : 0x{event['args']['contractHash'].hex()}")
        print(f"     Auditor: {event['args']['auditor']}")
        print(f"     Block  : {event['blockNumber']}")
        print("-" * 60)

except Exception as e:
    print(f"Method 1 failed: {e}")
    print("\nTrying Method 2...\n")

    # ==============================
    # METHOD 2: Manual get_logs fallback
    # ==============================
    try:
        latest_block = w3.eth.block_number

        logs = w3.eth.get_logs({
            "fromBlock": hex(0),          # hex format fixes Ganache issues
            "toBlock": hex(latest_block),
            "address": w3.to_checksum_address(registry_info["address"])
        })

        print(f"Total logs found: {len(logs)}\n")

        for log in logs:
            try:
                event = contract.events.ContractApproved().process_log(log)
                print(f"Hash   : 0x{event['args']['contractHash'].hex()}")
                print(f"Auditor: {event['args']['auditor']}")
                print(f"Block  : {log['blockNumber']}")
                print("-" * 60)
            except Exception as inner:
                print(f"Could not decode log: {inner}")
                continue

    except Exception as e2:
        print(f"Method 2 also failed: {e2}")

# ==============================
# QUICK SANITY CHECK
# ==============================
print("\n📊 Quick Stats:")
print(f"   Latest block number : {w3.eth.block_number}")
print(f"   Contract address    : {contract.address}")
print(f"   Connected           : {w3.is_connected()}")