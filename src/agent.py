from google.adk.agents import Agent
from google.adk.tools import google_search, FunctionTool
import json
import os
from datetime import datetime
import hashlib

from web3 import Web3
import requests

from dotenv import load_dotenv
load_dotenv()


RETAILER_WALLET_ADDRESS = os.getenv("AGENT_RETAILER_ONCHAIN_WALLET")  
print(f"Retailer Wallet Address: {RETAILER_WALLET_ADDRESS}")

# Inventory data
INVENTORY_ITEMS = [
    {"id": 1, "name": "Wireless Bluetooth Headphones", "price": 79.99, "stock": 25},
    {"id": 2, "name": "Smartphone Case (iPhone)", "price": 24.99, "stock": 50},
    {"id": 3, "name": "USB-C Charging Cable", "price": 12.99, "stock": 100},
    {"id": 4, "name": "Portable Power Bank 10000mAh", "price": 34.99, "stock": 30},
    {"id": 5, "name": "Bluetooth Speaker", "price": 59.99, "stock": 15},
    {"id": 6, "name": "Laptop Stand", "price": 45.99, "stock": 20},
    {"id": 7, "name": "Wireless Mouse", "price": 29.99, "stock": 40},
    {"id": 8, "name": "Screen Protector", "price": 9.99, "stock": 75},
    {"id": 9, "name": "Car Phone Mount", "price": 19.99, "stock": 35},
    {"id": 10, "name": "Gaming Keyboard", "price": 89.99, "stock": 12}
]

# Payment configuration
PAYMENT_CONFIG = {
    "supported_networks": {
        "ethereum": {
            "name": "Ethereum",
            "chain_id": 1,
            "wallet_address": RETAILER_WALLET_ADDRESS,
            "usdc_contract": "0xA0b86a33E6Fbe2E8b45C7D5e8B3F2F9B14E96C72",
            "network_fee": "High",
            "confirmation_time": "15 minutes"
        },
        "polygon": {
            "name": "Polygon (MATIC)",
            "chain_id": 137,
            "wallet_address": RETAILER_WALLET_ADDRESS,
            "usdc_contract": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "network_fee": "Low",
            "confirmation_time": "2-5 minutes"
        },
        "arbitrum": {
            "name": "Arbitrum One",
            "chain_id": 42161,
            "wallet_address": RETAILER_WALLET_ADDRESS,
            "usdc_contract": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "network_fee": "Very Low",
            "confirmation_time": "1-2 minutes"
        }
    },
    "default_network": "polygon",
    "minimum_payment": 1.00,
    "payment_timeout": "30 minutes"
}

class ConversationMemory:
    def __init__(self, memory_file="conversation_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.user_sessions = {}  # Maps user_id to current session_id
    
    def _load_memory(self):
        """Load conversation memory from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_memory(self):
        """Save conversation memory to file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def get_or_create_session_for_user(self, user_id, current_context_id=None):
        """Get existing session for user or create new one."""
        # Check if user has an active session
        if user_id in self.user_sessions:
            existing_session = self.user_sessions[user_id]
            # Check if session still exists in memory
            if existing_session in self.memory:
                return existing_session
        
        # Create new session or use current context
        if current_context_id:
            session_id = current_context_id
        else:
            # Generate a session ID based on user and timestamp
            session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
        self.user_sessions[user_id] = session_id
        return session_id
    
    def get_session_memory(self, session_id):
        """Get memory for a specific session."""
        return self.memory.get(session_id, {
            "conversation_history": [],
            "user_preferences": {},
            "past_searches": [],
            "payment_requests": [],
            "created_at": datetime.now().isoformat()
        })
    
    def get_user_conversation_history(self, user_id, limit=5):
        """Get recent conversation history across all sessions for a user."""
        all_conversations = []
        
        for session_id, session_data in self.memory.items():
            if session_id.startswith(user_id) or user_id in session_id:
                for conv in session_data.get("conversation_history", []):
                    all_conversations.append({
                        "session_id": session_id,
                        "timestamp": conv["timestamp"],
                        "user_query": conv["user_query"],
                        "agent_response": conv["agent_response"][:100] + "..." if len(conv["agent_response"]) > 100 else conv["agent_response"]
                    })
        
        # Sort by timestamp and return most recent
        all_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_conversations[:limit]
    
    def update_session_memory(self, session_id, user_query, agent_response, context=None):
        """Update memory for a session."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Add to conversation history
        self.memory[session_id]["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "agent_response": agent_response,
            "context": context
        })
        
        # Keep only last 15 conversations to prevent memory bloat
        if len(self.memory[session_id]["conversation_history"]) > 15:
            self.memory[session_id]["conversation_history"] = \
                self.memory[session_id]["conversation_history"][-15:]
        
        self._save_memory()
    
    def add_user_preference(self, session_id, preference_key, preference_value):
        """Add or update user preference."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["user_preferences"][preference_key] = preference_value
        self._save_memory()
    
    def add_search_history(self, session_id, search_term, results_count):
        """Add to search history."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["past_searches"].append({
            "timestamp": datetime.now().isoformat(),
            "search_term": search_term,
            "results_count": results_count
        })
        
        # Keep only last 20 searches
        if len(self.memory[session_id]["past_searches"]) > 20:
            self.memory[session_id]["past_searches"] = \
                self.memory[session_id]["past_searches"][-20:]
        
        self._save_memory()
    
    def add_payment_request(self, session_id, payment_data):
        """Add payment request to memory."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["payment_requests"].append(payment_data)
        self._save_memory()

# Global memory instance
conversation_memory = ConversationMemory()

def get_inventory():
    """Return the current inventory items."""
    return INVENTORY_ITEMS

def check_inventory(user_id: str, session_id: str):
    """Get current inventory with all items, prices, and stock levels."""
    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    inventory_text = "📦 **Current Inventory:**\n\n"
    for item in items:
        inventory_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
    
    # Update memory with this interaction
    conversation_memory.update_session_memory(
        actual_session_id, 
        "check_inventory", 
        inventory_text,
        {"action": "inventory_check", "items_count": len(items)}
    )
    
    return inventory_text

def search_product(product_name: str, user_id: str, session_id: str):
    """Search for a specific product in inventory by name."""

    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if product_name.lower() in item['name'].lower()]
    
    if not results:
        result_text = f"❌ No products found matching '{product_name}'"
    else:
        result_text = f"🔍 **Found {len(results)} product(s) matching '{product_name}':**\n\n"
        for item in results:
            result_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
    
    # Add to search history
    conversation_memory.add_search_history(actual_session_id, product_name, len(results))
    
    # Update memory with this interaction
    conversation_memory.update_session_memory(
        actual_session_id,
        f"search_product: {product_name}",
        result_text,
        {"action": "product_search", "search_term": product_name, "results_found": len(results)}
    )
    
    return result_text

def get_payment_info(network: str, user_id: str, session_id: str):
    """Get blockchain wallet address and payment information for USDC payments."""

    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    # Validate network
    if network.lower() not in PAYMENT_CONFIG["supported_networks"]:
        available_networks = ", ".join(PAYMENT_CONFIG["supported_networks"].keys())
        return f"❌ **Unsupported network.** Available networks: {available_networks}"
    
    network_info = PAYMENT_CONFIG["supported_networks"][network.lower()]
    
    payment_text = f"💳 **Payment Information - {network_info['name']}**\n\n"
    payment_text += f"**💰 Accepted Currency:** USDC only\n"
    payment_text += f"**🔗 Network:** {network_info['name']} (Chain ID: {network_info['chain_id']})\n"
    payment_text += f"**📍 Wallet Address:** `{network_info['wallet_address']}`\n"
    payment_text += f"**📄 USDC Contract:** `{network_info['usdc_contract']}`\n\n"
    
    payment_text += f"**📊 Network Details:**\n"
    payment_text += f"• Network Fee: {network_info['network_fee']}\n"
    payment_text += f"• Confirmation Time: {network_info['confirmation_time']}\n"
    payment_text += f"• Minimum Payment: ${PAYMENT_CONFIG['minimum_payment']:.2f} USDC\n"
    payment_text += f"• Payment Timeout: {PAYMENT_CONFIG['payment_timeout']}\n\n"
    
    payment_text += f"**⚠️ Important:**\n"
    payment_text += f"• Only send USDC tokens to this address\n"
    payment_text += f"• Ensure you're on the correct network ({network_info['name']})\n"
    payment_text += f"• Include your order reference in the transaction memo if possible\n"
    payment_text += f"• Double-check the wallet address before sending\n"
    
    # Store payment request in memory
    payment_data = {
        "timestamp": datetime.now().isoformat(),
        "network": network_info['name'],
        "wallet_address": network_info['wallet_address'],
        "user_id": user_id,
        "session_id": actual_session_id
    }
    conversation_memory.add_payment_request(actual_session_id, payment_data)
    
    # Update memory with this interaction
    conversation_memory.update_session_memory(
        actual_session_id,
        f"get_payment_info: {network}",
        payment_text,
        {"action": "payment_info_request", "network": network, "wallet_provided": True}
    )
    
    return payment_text

def get_supported_networks(user_id: str, session_id: str):
    """Get list of all supported blockchain networks for payments."""
    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    networks_text = "🌐 **Supported Payment Networks:**\n\n"
    
    for network_key, network_info in PAYMENT_CONFIG["supported_networks"].items():
        networks_text += f"**{network_info['name']}** ({network_key})\n"
        networks_text += f"• Chain ID: {network_info['chain_id']}\n"
        networks_text += f"• Network Fee: {network_info['network_fee']}\n"
        networks_text += f"• Confirmation Time: {network_info['confirmation_time']}\n\n"
    
    networks_text += f"**💡 Recommended:** {PAYMENT_CONFIG['supported_networks'][PAYMENT_CONFIG['default_network']]['name']} "
    networks_text += f"(Low fees, fast confirmations)\n\n"
    networks_text += f"**📝 To get payment address:** Ask for 'payment info' and specify the network\n"
    networks_text += f"Example: 'I want to pay with USDC on Polygon'\n"
    
    # Update memory with this interaction
    conversation_memory.update_session_memory(
        actual_session_id,
        "get_supported_networks",
        networks_text,
        {"action": "networks_info_request"}
    )
    
    return networks_text

def get_conversation_context(user_id: str, session_id: str):
    """Get conversation context and history for the user across sessions."""
    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    current_session_memory = conversation_memory.get_session_memory(actual_session_id)
    user_history = conversation_memory.get_user_conversation_history(user_id)
    
    if not user_history and not current_session_memory["conversation_history"]:
        return "🆕 **New conversation started.** How can I help you today?"
    
    context_text = "💭 **Your Conversation Context:**\n\n"
    
    # Show user preferences from current session
    if current_session_memory["user_preferences"]:
        context_text += "**Your Saved Preferences:**\n"
        for key, value in current_session_memory["user_preferences"].items():
            context_text += f"• {key}: {value}\n"
        context_text += "\n"
    
    # Show recent payment requests
    if current_session_memory["payment_requests"]:
        context_text += "**Recent Payment Requests:**\n"
        for payment in current_session_memory["payment_requests"][-2:]:
            context_text += f"• {payment['network']} - {payment['timestamp'][:10]}\n"
        context_text += "\n"
    
    # Show recent searches from current session
    if current_session_memory["past_searches"]:
        context_text += "**Recent Searches in This Session:**\n"
        for search in current_session_memory["past_searches"][-3:]:
            context_text += f"• '{search['search_term']}' ({search['results_count']} results)\n"
        context_text += "\n"
    
    # Show conversation history across sessions
    if user_history:
        context_text += "**Your Recent Conversations:**\n"
        for conv in user_history[:5]:  # Show last 5 conversations
            context_text += f"• You asked: {conv['user_query'][:60]}{'...' if len(conv['user_query']) > 60 else ''}\n"
        context_text += f"\n**Current Session ID:** {actual_session_id}\n"
    
    return context_text

def save_user_preference(preference_key: str, preference_value: str, user_id: str, session_id: str):
    """Save a user preference for future reference."""
    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    conversation_memory.add_user_preference(actual_session_id, preference_key, preference_value)
    return f"✅ **Preference saved:** {preference_key} = {preference_value} (Session: {actual_session_id})"

def start_new_session(user_id: str):
    """Start a new conversation session for the user."""
    # Generate new session ID
    new_session_id = f"{user_id}_{int(datetime.now().timestamp())}"
    conversation_memory.user_sessions[user_id] = new_session_id
    
    return f"🆕 **New session started!** Session ID: {new_session_id}\nYour previous conversations are still accessible for context."


def verify_usdc_payment(tx_hash: str, expected_amount: float, network: str, user_id: str, session_id: str):
    """Verify USDC payment transaction on blockchain."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    try:
        network_info = PAYMENT_CONFIG["supported_networks"][network.lower()]
        retailer_address = network_info["wallet_address"].lower()
        usdc_contract = network_info["usdc_contract"].lower()
        
        # Use public RPC endpoints
        rpc_urls = {
            "ethereum": "https://eth.llamarpc.com",
            "polygon": "https://polygon-rpc.com",
            "arbitrum": "https://arb1.arbitrum.io/rpc"
        }
        
        w3 = Web3(Web3.HTTPProvider(rpc_urls[network.lower()]))
        
        # Get transaction receipt
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx = w3.eth.get_transaction(tx_hash)
        
        # Check if transaction was successful
        if tx_receipt.status != 1:
            return f"❌ **Transaction failed** - Hash: {tx_hash}"
        
        # Verify it's a USDC transfer to our address
        payment_verified = False
        amount_received = 0
        
        for log in tx_receipt.logs:
            print(f"Log: {log}")
            if log.address.lower() == usdc_contract:
                # Decode Transfer event (to our address)
                if len(log.topics) >= 3:
                    to_address = "0x" + log.topics[2].hex()[-40:]
                    if to_address.lower() == retailer_address:
                        # USDC has 6 decimals
                        amount_received = int(log.data, 16) / 1000000
                        payment_verified = True
                        break
        
        if not payment_verified:
            return f"❌ **Payment not found** - No USDC transfer to our address in transaction {tx_hash}"
        
        if amount_received < expected_amount:
            return f"❌ **Insufficient payment** - Expected: ${expected_amount:.2f} USDC, Received: ${amount_received:.2f} USDC"
        
        # Store successful payment
        payment_data = {
            "timestamp": datetime.now().isoformat(),
            "tx_hash": tx_hash,
            "network": network_info['name'],
            "amount_usdc": amount_received,
            "expected_amount": expected_amount,
            "status": "verified",
            "user_id": user_id
        }
        conversation_memory.add_payment_request(actual_session_id, payment_data)
        
        result_text = f"✅ **Payment Verified!**\n\n"
        result_text += f"• Transaction: {tx_hash}\n"
        result_text += f"• Network: {network_info['name']}\n"
        result_text += f"• Amount: ${amount_received:.2f} USDC\n"
        result_text += f"• Status: Confirmed\n\n"
        result_text += f"Thank you for your payment! Your order will be processed."
        
        return result_text
        
    except Exception as e:
        return f"❌ **Verification failed** - Error: {str(e)}"

verify_payment_tool = FunctionTool(func=verify_usdc_payment)

# Add to tool_List
# tool_List = [check_tool, search_tool, payment_tool, networks_tool, verify_payment_tool, context_tool, preference_tool,
check_tool = FunctionTool(func=check_inventory)
search_tool = FunctionTool(func=search_product)
payment_tool = FunctionTool(func=get_payment_info)
networks_tool = FunctionTool(func=get_supported_networks)
context_tool = FunctionTool(func=get_conversation_context)
preference_tool = FunctionTool(func=save_user_preference)
new_session_tool = FunctionTool(func=start_new_session)

tool_List = [check_tool, search_tool, payment_tool, networks_tool, context_tool, preference_tool, new_session_tool, verify_payment_tool]

Retailer_Root_Agent = Agent(
    name="retailer_agent",
    model="gemini-2.5-flash-lite-preview-06-17",
    description="Agent to handle retail-related queries and provide information about inventory with conversation memory and USDC payment processing.",
instruction=(
    "You are a Retailer Agent for an electronics retail store with persistent conversation memory and USDC payment capabilities. "
    "You can remember conversations across multiple sessions for each user.\n\n"
    "Use the available tools to help customers:\n"
    "- Use 'check_inventory' to show all available products\n"
    "- Use 'search_product' to find specific items\n"
    "- Use 'get_payment_info' to provide blockchain wallet address for USDC payments (specify network: ethereum, polygon, or arbitrum)\n"
    "- Use 'get_supported_networks' to show all available payment networks\n"
    "- Use 'verify_usdc_payment' to verify blockchain payment transactions (requires tx_hash, expected_amount, and network)\n"
    "- Use 'get_conversation_context' to recall previous conversations and user preferences across sessions\n"
    "- Use 'save_user_preference' to remember customer preferences for future interactions\n"
    "- Use 'start_new_session' to begin a fresh conversation while keeping access to history\n\n"
    "PAYMENT IMPORTANT: We ONLY accept USDC (USD Coin) payments on supported blockchain networks. "
    "When customers ask about payment, always use the payment tools to provide accurate wallet addresses and network information. "
    "Recommend Polygon network for lower fees and faster confirmations unless customer specifies otherwise. "
    "When customers provide transaction hash for payment verification, use 'verify_usdc_payment' to confirm the payment.\n\n"
    "IMPORTANT: Always extract the user_id from the query context (look for Session ID or user info) "
    "and pass it to tool functions to maintain conversation continuity.\n\n"
    "Always start by checking conversation context to provide personalized service. "
    "Remember user preferences like favorite product categories, budget ranges, payment network preferences, or specific needs. "
    "Reference previous searches and conversations to provide better recommendations. "
    "Acknowledge when you remember previous interactions to show continuity."
),
    tools=tool_List,
)