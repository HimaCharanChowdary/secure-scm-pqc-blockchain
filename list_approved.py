from web3 import Web3
import json
import hashlib
import os

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

contract = w3.eth.contract(
    address=registry_info["address"],
    abi=registry_info["abi"]
)

# Check a specific contract file
file_path = "sample_dataset\contract_5.sol"

with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    source_code = f.read()

contract_hash = hashlib.sha256(source_code.encode()).digest()

is_approved = contract.functions.isApproved(contract_hash).call()

print("Contract:", file_path)
print("Hash:", contract_hash.hex())
print("Approved?", is_approved)