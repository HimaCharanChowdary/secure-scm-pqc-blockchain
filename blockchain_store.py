from web3 import Web3
import json
import hashlib

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("registry_info.json") as f:
    registry_info = json.load(f)

contract_address = registry_info["address"]
abi = json.loads(registry_info["abi"])   
registry = w3.eth.contract(address=contract_address, abi=abi)
account = w3.eth.accounts[0]

def store_contract(source_code):
    contract_hash = hashlib.sha256(source_code.encode()).digest()

    tx_hash = registry.functions.approveContract(contract_hash).transact({
        "from": account
    })

    w3.eth.wait_for_transaction_receipt(tx_hash)

    print("Stored on blockchain:", contract_hash.hex())