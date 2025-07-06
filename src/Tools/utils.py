from datetime import datetime
from Tools.memory import conversation_memory
from dotenv import load_dotenv
import os

from inventories import INVENTORY_ITEMS
load_dotenv()


RETAILER_WALLET_ADDRESS = os.getenv("AGENT_RETAILER_ONCHAIN_WALLET")  
print(f"Retailer Wallet Address: {RETAILER_WALLET_ADDRESS}")


# Payment configuration
PAYMENT_CONFIG = {
    "supported_networks": {
        "sepolia": {
            "name": "Sepolia Testnet",
            "chain_id": 11155111,
            "wallet_address": RETAILER_WALLET_ADDRESS,
            "usdt_contract": "0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0",
            "rpc_url": "https://ethereum-sepolia-rpc.publicnode.com",
            "network_fee": "Low (Testnet)",
            "confirmation_time": "1-2 minutes"
        }
    },
    "default_network": "sepolia",
    "minimum_payment": 1.00,
    "payment_timeout": "30 minutes"
}




def get_payment_info(network: str, user_id: str, session_id: str):
    """Get blockchain wallet address and payment information for USDT payments."""

    # Get proper session for user
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    # Validate network
    if network.lower() not in PAYMENT_CONFIG["supported_networks"]:
        available_networks = ", ".join(PAYMENT_CONFIG["supported_networks"].keys())
        return f"❌ **Unsupported network.** Available networks: {available_networks}"
    
    network_info = PAYMENT_CONFIG["supported_networks"][network.lower()]
    
    payment_text = f"💳 **Payment Information - {network_info['name']}**\n\n"
    payment_text += f"**💰 Accepted Currency:** USDT only\n"
    payment_text += f"**🔗 Network:** {network_info['name']} (Chain ID: {network_info['chain_id']})\n"
    payment_text += f"**📍 Wallet Address:** `{network_info['wallet_address']}`\n"
    payment_text += f"**📄 USDT Contract:** `{network_info['usdt_contract']}`\n\n"
    
    payment_text += f"**📊 Network Details:**\n"
    payment_text += f"• Network Fee: {network_info['network_fee']}\n"
    payment_text += f"• Confirmation Time: {network_info['confirmation_time']}\n"
    payment_text += f"• Minimum Payment: ${PAYMENT_CONFIG['minimum_payment']:.2f} USDT\n"
    payment_text += f"• Payment Timeout: {PAYMENT_CONFIG['payment_timeout']}\n\n"
    
    payment_text += f"**⚠️ Important:**\n"
    payment_text += f"• Only send USDT tokens to this address\n"
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


def verify_usdt_payment(tx_hash: str, expected_amount: float, network: str, user_id: str, session_id: str):
    """Verify USDT payment transaction on Sepolia blockchain."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    try:
        network_info = PAYMENT_CONFIG["supported_networks"][network.lower()]
        retailer_address = network_info["wallet_address"].lower()
        usdt_contract = network_info["usdt_contract"].lower()
        rpc_url = network_info["rpc_url"]
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Get transaction receipt
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx = w3.eth.get_transaction(tx_hash)
        
        # Check if transaction was successful
        if tx_receipt.status != 1:
            return f"❌ **Transaction failed** - Hash: {tx_hash}"
        
        # Verify it's a USDT transfer to our address
        payment_verified = False
        amount_received = 0
        
        for log in tx_receipt.logs:
            print(f"Log: {log}")
            if log.address.lower() == usdt_contract:
                # Decode Transfer event (to our address)
                if len(log.topics) >= 3:
                    to_address = "0x" + log.topics[2].hex()[-40:]
                    if to_address.lower() == retailer_address:
                        # USDT has 6 decimals
                        amount_received = int(log.data, 16) / 1000000
                        payment_verified = True
                        break
        
        if not payment_verified:
            return f"❌ **Payment not found** - No USDT transfer to our address in transaction {tx_hash}"
        
        if amount_received < expected_amount:
            return f"❌ **Insufficient payment** - Expected: ${expected_amount:.2f} USDT, Received: ${amount_received:.2f} USDT"
        
        # Store successful payment
        payment_data = {
            "timestamp": datetime.now().isoformat(),
            "tx_hash": tx_hash,
            "network": network_info['name'],
            "amount_usdt": amount_received,
            "expected_amount": expected_amount,
            "status": "verified",
            "user_id": user_id
        }
        conversation_memory.add_payment_request(actual_session_id, payment_data)
        
        result_text = f"✅ **Payment Verified!**\n\n"
        result_text += f"• Transaction: {tx_hash}\n"
        result_text += f"• Network: {network_info['name']}\n"
        result_text += f"• Amount: ${amount_received:.2f} USDT\n"
        result_text += f"• Status: Confirmed\n\n"
        result_text += f"Thank you for your payment! Your order will be processed."
        
        return result_text
        
    except Exception as e:
        return f"❌ **Verification failed** - Error: {str(e)}"

def get_product_details(product_name: str, user_id: str, session_id: str):
    """Get detailed information about a specific product including specs, features, and reviews."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    product = None
    
    for item in items:
        if product_name.lower() in item['name'].lower():
            product = item
            break
    
    if not product:
        return f"❌ Product '{product_name}' not found in inventory."
    
    details_text = f"📋 **Product Details: {product['name']}**\n\n"
    details_text += f"**Brand:** {product.get('brand', 'N/A')}\n"
    details_text += f"**Model:** {product.get('model', 'N/A')}\n"
    details_text += f"**Price:** ${product['price']:.2f}\n"
    details_text += f"**Stock:** {product['stock']} units\n"
    details_text += f"**Category:** {product.get('category', 'N/A')}\n\n"
    
    if product.get('description'):
        details_text += f"**Description:**\n{product['description']}\n\n"
    
    if product.get('specifications'):
        details_text += f"**Specifications:**\n"
        for key, value in product['specifications'].items():
            details_text += f"• {key.replace('_', ' ').title()}: {value}\n"
        details_text += "\n"
    
    if product.get('features'):
        details_text += f"**Key Features:**\n"
        for feature in product['features']:
            details_text += f"• {feature}\n"
        details_text += "\n"
    
    if product.get('rating'):
        details_text += f"**Customer Rating:** ⭐ {product['rating']}/5 ({product.get('review_count', 0)} reviews)\n"
    
    if product.get('top_review'):
        details_text += f"**Top Review:** \"{product['top_review']}\"\n\n"
    
    if product.get('warranty'):
        details_text += f"**Warranty:** {product['warranty']}\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"get_product_details: {product_name}",
        details_text,
        {"action": "product_details", "product_id": product['id']}
    )
    
    return details_text

def search_by_category(category: str, user_id: str, session_id: str):
    """Search products by category (e.g., Audio, Mobile Accessories, Gaming, etc.)."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if category.lower() in item.get('category', '').lower()]
    
    if not results:
        available_categories = list(set([item.get('category', 'Unknown') for item in items]))
        return f"❌ No products found in category '{category}'\n\n**Available categories:** {', '.join(available_categories)}"
    
    category_text = f"🗂️ **Products in '{category}' category ({len(results)} items):**\n\n"
    for item in results:
        category_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
        if item.get('rating'):
            category_text += f"  ⭐ {item['rating']}/5 stars\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"search_by_category: {category}",
        category_text,
        {"action": "category_search", "category": category, "results_found": len(results)}
    )
    
    return category_text

def search_by_price_range(min_price: float, max_price: float, user_id: str, session_id: str):
    """Search products within a specific price range."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if min_price <= item['price'] <= max_price]
    
    if not results:
        return f"❌ No products found in price range ${min_price:.2f} - ${max_price:.2f}"
    
    price_text = f"💰 **Products in price range ${min_price:.2f} - ${max_price:.2f} ({len(results)} items):**\n\n"
    
    # Sort by price
    results.sort(key=lambda x: x['price'])
    
    for item in results:
        price_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
        price_text += f"  Category: {item.get('category', 'N/A')}\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"search_by_price_range: ${min_price}-${max_price}",
        price_text,
        {"action": "price_search", "min_price": min_price, "max_price": max_price, "results_found": len(results)}
    )
    
    return price_text

def search_by_brand(brand: str, user_id: str, session_id: str):
    """Search products by brand name."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if brand.lower() in item.get('brand', '').lower()]
    
    if not results:
        available_brands = list(set([item.get('brand', 'Unknown') for item in items if item.get('brand')]))
        return f"❌ No products found from brand '{brand}'\n\n**Available brands:** {', '.join(available_brands)}"
    
    brand_text = f"🏷️ **Products from '{brand}' ({len(results)} items):**\n\n"
    for item in results:
        brand_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
        brand_text += f"  Model: {item.get('model', 'N/A')}\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"search_by_brand: {brand}",
        brand_text,
        {"action": "brand_search", "brand": brand, "results_found": len(results)}
    )
    
    return brand_text

def get_top_rated_products(user_id: str, session_id: str, min_rating: float = 4.0):
    """Get top-rated products with ratings above specified threshold."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if item.get('rating', 0) >= min_rating]
    
    if not results:
        return f"❌ No products found with rating {min_rating}/5 or higher"
    
    # Sort by rating (highest first)
    results.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    rating_text = f"⭐ **Top-Rated Products ({min_rating}+ stars, {len(results)} items):**\n\n"
    for item in results:
        rating_text += f"• **{item['name']}** - ${item['price']:.2f}\n"
        rating_text += f"  ⭐ {item['rating']}/5 ({item.get('review_count', 0)} reviews)\n"
        rating_text += f"  Stock: {item['stock']} units\n\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"get_top_rated_products: {min_rating}+",
        rating_text,
        {"action": "top_rated_search", "min_rating": min_rating, "results_found": len(results)}
    )
    
    return rating_text

def search_by_feature(feature: str, user_id: str, session_id: str):
    """Search products that have a specific feature."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = []
    
    for item in items:
        item_features = item.get('features', [])
        if any(feature.lower() in str(f).lower() for f in item_features):
            results.append(item)
    
    if not results:
        return f"❌ No products found with feature '{feature}'"
    
    feature_text = f"🔍 **Products with '{feature}' feature ({len(results)} items):**\n\n"
    for item in results:
        feature_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
        matching_features = [f for f in item.get('features', []) if feature.lower() in str(f).lower()]
        feature_text += f"  Features: {', '.join(matching_features)}\n\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"search_by_feature: {feature}",
        feature_text,
        {"action": "feature_search", "feature": feature, "results_found": len(results)}
    )
    
    return feature_text

def get_low_stock_items(user_id: str, session_id: str, threshold: int = 20):
    """Get items with low stock levels."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    results = [item for item in items if item['stock'] <= threshold]
    
    if not results:
        return f"✅ All products have sufficient stock (above {threshold} units)"
    
    # Sort by stock level (lowest first)
    results.sort(key=lambda x: x['stock'])
    
    stock_text = f"⚠️ **Low Stock Alert (≤{threshold} units, {len(results)} items):**\n\n"
    for item in results:
        stock_text += f"• **{item['name']}** - ${item['price']:.2f}\n"
        stock_text += f"  🔴 Only {item['stock']} units remaining!\n\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"get_low_stock_items: ≤{threshold}",
        stock_text,
        {"action": "low_stock_check", "threshold": threshold, "low_stock_count": len(results)}
    )
    
    return stock_text

def get_product_reviews(product_name: str, user_id: str, session_id: str):
    """Get customer reviews and ratings for a specific product."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    product = None
    
    for item in items:
        if product_name.lower() in item['name'].lower():
            product = item
            break
    
    if not product:
        return f"❌ Product '{product_name}' not found in inventory."
    
    if not product.get('rating'):
        return f"📝 No customer reviews available for '{product['name']}' yet."
    
    review_text = f"📝 **Customer Reviews: {product['name']}**\n\n"
    review_text += f"**Overall Rating:** ⭐ {product['rating']}/5.0\n"
    review_text += f"**Total Reviews:** {product.get('review_count', 0)}\n\n"
    
    if product.get('top_review'):
        review_text += f"**Featured Review:**\n\"{product['top_review']}\"\n\n"
    
    # Add rating breakdown simulation
    rating_breakdown = {
        5: int(product.get('review_count', 0) * 0.4),
        4: int(product.get('review_count', 0) * 0.3),
        3: int(product.get('review_count', 0) * 0.2),
        2: int(product.get('review_count', 0) * 0.08),
        1: int(product.get('review_count', 0) * 0.02)
    }
    
    review_text += f"**Rating Breakdown:**\n"
    for stars in range(5, 0, -1):
        count = rating_breakdown[stars]
        percentage = (count / product.get('review_count', 1)) * 100
        review_text += f"{stars}⭐: {count} reviews ({percentage:.1f}%)\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"get_product_reviews: {product_name}",
        review_text,
        {"action": "product_reviews", "product_id": product['id']}
    )
    
    return review_text

def compare_products(product1: str, product2: str, user_id: str, session_id: str):
    """Compare two products side by side."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    items = get_inventory()
    prod1 = None
    prod2 = None
    
    for item in items:
        if product1.lower() in item['name'].lower():
            prod1 = item
        if product2.lower() in item['name'].lower():
            prod2 = item
    
    if not prod1:
        return f"❌ Product '{product1}' not found in inventory."
    if not prod2:
        return f"❌ Product '{product2}' not found in inventory."
    
    compare_text = f"⚖️ **Product Comparison**\n\n"
    compare_text += f"**Product A: {prod1['name']}**\n"
    compare_text += f"• Price: ${prod1['price']:.2f}\n"
    compare_text += f"• Brand: {prod1.get('brand', 'N/A')}\n"
    compare_text += f"• Category: {prod1.get('category', 'N/A')}\n"
    compare_text += f"• Rating: {prod1.get('rating', 'N/A')}/5\n"
    compare_text += f"• Stock: {prod1['stock']} units\n\n"
    
    compare_text += f"**Product B: {prod2['name']}**\n"
    compare_text += f"• Price: ${prod2['price']:.2f}\n"
    compare_text += f"• Brand: {prod2.get('brand', 'N/A')}\n"
    compare_text += f"• Category: {prod2.get('category', 'N/A')}\n"
    compare_text += f"• Rating: {prod2.get('rating', 'N/A')}/5\n"
    compare_text += f"• Stock: {prod2['stock']} units\n\n"
    
    price_diff = abs(prod1['price'] - prod2['price'])
    cheaper = prod1 if prod1['price'] < prod2['price'] else prod2
    compare_text += f"**Price Difference:** ${price_diff:.2f} ({cheaper['name']} is cheaper)\n"
    
    conversation_memory.update_session_memory(
        actual_session_id,
        f"compare_products: {product1} vs {product2}",
        compare_text,
        {"action": "product_comparison", "product1_id": prod1['id'], "product2_id": prod2['id']}
    )
    
    return compare_text
