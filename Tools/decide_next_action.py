import re


def decide_next_action(current_context: str, retailer_response: str, shopping_goal: str, budget: float, user_id: str, session_id: str):
    """Decide what the buyer should do next based on the context."""
    
    # Be direct and focused on the specific goal
    if not retailer_response:
        return f"I want to buy {shopping_goal}. Do you have it in stock? My budget is ${budget}."
    
    lower_response = retailer_response.lower()
    
    # Look for wallet address in response
    wallet_pattern = r'0x[a-fA-F0-9]{40}'
    wallet_addresses = re.findall(wallet_pattern, retailer_response)
    
    # Check if wallet address was provided in current OR previous responses
    context_wallet_addresses = re.findall(wallet_pattern, current_context)
    all_wallet_addresses = wallet_addresses + context_wallet_addresses
    
    # Extract price from response or context
    price_pattern = r'\$(\d+(?:\.\d{2})?)'
    prices = re.findall(price_pattern, retailer_response)
    if not prices:
        prices = re.findall(price_pattern, current_context)
    
    # Check if payment was already executed (look for transaction hash in context)
    hash_pattern = r'0x[a-fA-F0-9]{64}'
    context_hashes = re.findall(hash_pattern, current_context)
    # Fix the boolean iteration error
    payment_already_made = ("PAYMENT SUCCESSFUL" in current_context or 
                           "✅" in current_context or 
                           "EXECUTE_PAYMENT" in current_context)
    
    # If payment already made and retailer is asking for shipping address
    if (payment_already_made or context_hashes) and any(phrase in lower_response for phrase in 
           ["shipping address", "delivery address", "full name", "street address", "provide"]):
        if context_hashes:
            return f"PROVIDE_SHIPPING_ADDRESS:{context_hashes[0]}"
        else:
            return "PROVIDE_SHIPPING_ADDRESS:dummy_hash"
    
    # Check for explicit payment confirmation from retailer
    if any(phrase in lower_response for phrase in 
           ["payment received", "payment confirmed", "transaction confirmed"]):
        if context_hashes:
            return f"PROVIDE_SHIPPING_ADDRESS:{context_hashes[0]}"
        else:
            return "Great! Payment confirmed. Please let me provide my shipping address for delivery."
    
    # Check if the specific product is mentioned
    goal_keywords = shopping_goal.lower().split()
    has_product = any(keyword in lower_response for keyword in goal_keywords if len(keyword) > 3)
    
    # Check if previous payment failed and need to retry
    if ("payment failed" in lower_response or "transaction hash" in lower_response or 
        "not found" in lower_response or "invalid" in lower_response or 
        "timeout" in lower_response) and all_wallet_addresses and prices:
        price = float(prices[0])
        if price <= budget:
            wallet_address = all_wallet_addresses[0]
            return f"EXECUTE_PAYMENT:${price} to {wallet_address} for {shopping_goal}. Retrying payment now..."
        else:
            return f"I understand there was a payment issue, but ${price} is over my ${budget} budget."
    
    # Check if retailer is asking for transaction hash (payment already attempted)
    if "transaction hash" in lower_response or "hash" in lower_response:
        if all_wallet_addresses and prices:
            price = float(prices[0])
            wallet_address = all_wallet_addresses[0]
            return f"EXECUTE_PAYMENT:${price} to {wallet_address} for {shopping_goal}. Processing payment now..."
        else:
            return "Let me retry the payment with correct details."
    
    # MAIN PAYMENT LOGIC: If we have both wallet and price, execute payment
    if all_wallet_addresses and prices and not payment_already_made:
        price = float(prices[0])
        if price <= budget:
            wallet_address = all_wallet_addresses[0]
            # Signal to execute payment
            return f"EXECUTE_PAYMENT:${price} to {wallet_address} for {shopping_goal}. Processing payment now..."
        else:
            return f"${price} is over my ${budget} budget."
    
    elif all_wallet_addresses and not prices:
        # Have wallet but need price confirmation
        return f"I see your wallet address. Just to confirm, the total for {shopping_goal} is how much? I'll send the USDT payment once confirmed."
    
    elif wallet_addresses and ("$" in retailer_response or "price" in lower_response):
        # Just got wallet address with price info
        if prices:
            price = float(prices[0])
            if price <= budget:
                wallet_address = wallet_addresses[0]
                return f"EXECUTE_PAYMENT:${price} to {wallet_address} for {shopping_goal}. Processing payment now..."
            else:
                return f"${price} is over my ${budget} budget."
        else:
            return f"Great! I have your wallet address. What's the final price for {shopping_goal}?"
    
    elif has_product and ("$" in retailer_response or "price" in lower_response):
        # Extract price if possible
        if prices:
            price = float(prices[0])
            if price <= budget:
                return f"Perfect! I'll take the {shopping_goal} for ${price}. Please provide your Sepolia USDT wallet address so I can send the payment."
            else:
                return f"${price} is over my ${budget} budget. Do you have {shopping_goal} at a lower price?"
        else:
            return f"What's the price for {shopping_goal}?"
    
    elif "payment" in lower_response or "USDT" in lower_response or "wallet" in lower_response:
        if not wallet_addresses and not context_wallet_addresses:
            return "I can pay with USDT on Sepolia blockchain. Please provide your Sepolia wallet address."
        else:
            return "I see you've provided the wallet information. Let me proceed with the payment."
    
    elif "stock" in lower_response or "inventory" in lower_response:
        if has_product:
            return f"Great! What's the price for {shopping_goal}?"
        else:
            return f"Do you have {shopping_goal} specifically?"
    
    elif "don't have" in lower_response or "out of stock" in lower_response or "not available" in lower_response:
        return "Okay, thank you. I'm only looking for that specific item."
    
    else:
        # Be more direct
        return f"I specifically need {shopping_goal}. Do you have this exact product and what's the price?"