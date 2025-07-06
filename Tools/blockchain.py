

import os
from dotenv import load_dotenv

from web3 import Web3
from eth_account import Account

from Tools.utils import print_system


load_dotenv()



# Add USDT contract details for Sepolia
Sepolia_RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
USDT_CONTRACT_ADDRESS = "0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0"  # USDT on Sepolia
USDT_DECIMALS = 6

# USDT ABI (minimal for transfer function)
USDT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]


def send_USDT_payment(recipient_address: str, amount: float, user_id: str, session_id: str):
    """Send USDT payment on Sepolia blockchain and wait for confirmation."""
    try:
        # Get private key from environment
        private_key = os.environ.get('BUYER_WALLET_PRIVATE_KEY')
        if not private_key:
            return "❌ ERROR: BUYER_WALLET_PRIVATE_KEY not found in environment variables"
        
        # Connect to Sepolia
        w3 = Web3(Web3.HTTPProvider(Sepolia_RPC_URL))
        if not w3.is_connected():
            return "❌ ERROR: Cannot connect to Sepolia network"
        
        # Get account from private key
        account = Account.from_key(private_key)
        buyer_address = account.address
        
        # Validate recipient address
        if not Web3.is_address(recipient_address):
            return f"❌ ERROR: Invalid recipient address: {recipient_address}"
        
        recipient_address = Web3.to_checksum_address(recipient_address)
        
        # Get USDT contract
        USDT_contract = w3.eth.contract(
            address=Web3.to_checksum_address(USDT_CONTRACT_ADDRESS),
            abi=USDT_ABI
        )
        
        # Check USDT balance
        balance = USDT_contract.functions.balanceOf(buyer_address).call()
        balance_USDT = balance / (10 ** USDT_DECIMALS)
        
        if balance_USDT < amount:
            return f"❌ ERROR: Insufficient USDT balance. Have: ${balance_USDT:.2f}, Need: ${amount}"
        
        # Convert amount to wei (USDT has 6 decimals)
        amount_wei = int(amount * (10 ** USDT_DECIMALS))
        
        # Build transaction
        transaction = USDT_contract.functions.transfer(
            recipient_address,
            amount_wei
        ).build_transaction({
            'from': buyer_address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(buyer_address),
            'chainId': 11155111  # Sepolia chain ID
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Send transaction - handle both old and new Web3.py versions
        try:
            # Try new version first (raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        except AttributeError:
            # Fall back to old version (rawTransaction)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        tx_hash_hex = tx_hash.hex()
        
        # Wait for transaction confirmation (up to 5 minutes)
        print_system(f"Transaction sent: {tx_hash_hex}. Waiting for confirmation...")
        
        max_wait_time = 300  # 5 minutes
        check_interval = 10  # Check every 10 seconds
        waited_time = 0
        
        while waited_time < max_wait_time:
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    return f"✅ PAYMENT SUCCESSFUL! ${amount} USDT sent to {recipient_address}. Transaction confirmed: {tx_hash_hex} (Block: {receipt.blockNumber})"
                else:
                    return f"❌ PAYMENT FAILED! Transaction {tx_hash_hex} failed on blockchain. Please try again."
            except:
                # Transaction not yet mined
                import time
                time.sleep(check_interval)
                waited_time += check_interval
                if waited_time % 30 == 0:  # Update every 30 seconds
                    print_system(f"Still waiting for confirmation... ({waited_time}s elapsed)")
        
        # Timeout - transaction taking too long
        return f"⏳ PAYMENT TIMEOUT: Transaction {tx_hash_hex} sent but confirmation taking longer than expected. Please check manually or retry."
        
    except Exception as e:
        return f"❌ ERROR: Payment failed - {str(e)}"

def check_payment_status(tx_hash: str, user_id: str, session_id: str):
    """Check the status of a payment transaction."""
    try:
        w3 = Web3(Web3.HTTPProvider(Sepolia_RPC_URL))
        if not w3.is_connected():
            return "❌ ERROR: Cannot connect to Sepolia network"
        
        # Get transaction receipt
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt.status == 1:
                return f"✅ PAYMENT CONFIRMED! Transaction {tx_hash} successful. Block: {receipt.blockNumber}"
            else:
                return f"❌ PAYMENT FAILED! Transaction {tx_hash} failed."
        except:
            return f"⏳ PAYMENT PENDING: Transaction {tx_hash} not yet confirmed. Please wait..."
            
    except Exception as e:
        return f"❌ ERROR: Cannot check payment status - {str(e)}"


def get_wallet_info(user_id: str, session_id: str):
    """Get buyer's wallet information."""
    try:
        private_key = os.getenv('BUYER_WALLET_PRIVATE_KEY')
        if not private_key:
            return "❌ ERROR: BUYER_WALLET_PRIVATE_KEY not found in environment variables"
        
        w3 = Web3(Web3.HTTPProvider(Sepolia_RPC_URL))
        account = Account.from_key(private_key)
        buyer_address = account.address
        
        # Get USDT balance
        USDT_contract = w3.eth.contract(
            address=Web3.to_checksum_address(USDT_CONTRACT_ADDRESS),
            abi=USDT_ABI
        )
        balance = USDT_contract.functions.balanceOf(buyer_address).call()
        balance_USDT = balance / (10 ** USDT_DECIMALS)
        
        # Get ETH balance for gas
        eth_balance = w3.eth.get_balance(buyer_address)
        eth_balance_formatted = w3.from_wei(eth_balance, 'ether')
        
        return f"💰 Wallet: {buyer_address}\n💵 USDT Balance: ${balance_USDT:.2f}\n⛽ ETH Balance: {eth_balance_formatted:.4f} (for gas)"
        
    except Exception as e:
        return f"❌ ERROR: Cannot get wallet info - {str(e)}"

