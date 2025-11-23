# blockchain.py
import json
from web3 import Web3
from pathlib import Path

cfg = json.load(open(Path(__file__).parent / "config.json"))
w3 = Web3(Web3.HTTPProvider(cfg["provider_url"]))
contract = w3.eth.contract(address=Web3.toChecksumAddress(cfg["contract_address"]), abi=cfg["contract_abi"])
owner_account = w3.eth.account.from_key(cfg["owner_private_key"])
CHAIN_ID = w3.eth.chain_id

def send_tx(function_tx):
    """Sign and send a transaction to the chain. function_tx is contract.functions.xxx(...).buildTransaction(...)"""
    signed = owner_account.sign_transaction(function_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return receipt

def add_or_update_product(product_id: int, quantity: int):
    fn = contract.functions.addOrUpdateProduct(product_id, quantity)
    tx = fn.buildTransaction({
        "from": owner_account.address,
        "nonce": w3.eth.get_transaction_count(owner_account.address),
        "gas": 300000,
        "gasPrice": w3.eth.gas_price
    })
    return send_tx(tx)

def restock(product_id: int, quantity: int):
    fn = contract.functions.restock(product_id, quantity)
    tx = fn.buildTransaction({
        "from": owner_account.address,
        "nonce": w3.eth.get_transaction_count(owner_account.address),
        "gas": 200000,
        "gasPrice": w3.eth.gas_price
    })
    return send_tx(tx)

def apply_discount_on_chain(product_id: int):
    fn = contract.functions.applyDiscount(product_id)
    tx = fn.buildTransaction({
        "from": owner_account.address,
        "nonce": w3.eth.get_transaction_count(owner_account.address),
        "gas": 150000,
        "gasPrice": w3.eth.gas_price
    })
    return send_tx(tx)
