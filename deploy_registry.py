from web3 import Web3
import subprocess
import json
import tempfile
import os

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

print("Connected:", w3.is_connected())

account = w3.eth.accounts[0]

# Solidity source
contract_source = """
pragma solidity ^0.4.24;

contract AuditRegistry {

    struct Record {
        address auditor;
        uint timestamp;
    }

    mapping(bytes32 => Record) public approvedContracts;

    event ContractApproved(bytes32 contractHash, address auditor);

    function approveContract(bytes32 contractHash) public {
        approvedContracts[contractHash] = Record(msg.sender, now);
        emit ContractApproved(contractHash, msg.sender);
    }

    function isApproved(bytes32 contractHash) public view returns (bool) {
        return approvedContracts[contractHash].timestamp != 0;
    }
}
"""

# Write temporary Solidity file
with tempfile.NamedTemporaryFile(delete=False, suffix=".sol") as sol_file:
    sol_file.write(contract_source.encode())
    sol_path = sol_file.name

# Compile using solc
compiled = subprocess.check_output(
    ["solc", "--combined-json", "abi,bin", sol_path]
)

compiled_json = json.loads(compiled)

contract_key = list(compiled_json["contracts"].keys())[0]
abi = compiled_json["contracts"][contract_key]["abi"]
bytecode = compiled_json["contracts"][contract_key]["bin"]

# Deploy
AuditRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)

tx_hash = AuditRegistry.constructor().transact({
    "from": account
})

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

contract_address = tx_receipt.contractAddress

print("Contract deployed at:", contract_address)

# Save ABI + address for later use
with open("registry_info.json", "w") as f:
    json.dump({
        "address": contract_address,
        "abi": abi
    }, f, indent=4)

os.remove(sol_path)