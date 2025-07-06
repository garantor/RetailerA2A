import re
from dotenv import load_dotenv
from typing import Optional


# Tool functions for the buyer agent
def analyze_retailer_response(response_text: str, budget: float, shopping_goal: str, user_id: str, session_id: str):
    """Analyze retailer's response and determine next action."""
    analysis = f"Analyzing retailer response: '{response_text[:100]}...' with budget ${budget} and goal: {shopping_goal}"
    
    # Simple logic to determine next steps
    if "payment" in response_text.lower() or "USDT" in response_text.lower():
        return f"Retailer is discussing payment options. Should consider if ready to purchase within budget of ${budget}."
    elif "price" in response_text.lower() and "$" in response_text:
        return "Retailer provided pricing information. Should evaluate if prices fit budget."
    elif "inventory" in response_text.lower() or "stock" in response_text.lower():
        return "Retailer showed inventory. Should look for items matching shopping goal."
    else:
        return "General retailer response. Should continue conversation to find suitable products."


def update_shopping_context(new_info: str, user_id: str, session_id: str):
    """Update shopping context with new information."""
    return f"Updated shopping context with: {new_info}"

def generate_buyer_response(context: str, goal: str, budget: float, user_id: str, session_id: str):
    """Generate appropriate buyer response based on context."""
    if "inventory" in context.lower():
        return "I'd like to see what products you have available that might match my needs."
    elif "payment" in context.lower():
        return "I'm interested in making a purchase. What are the payment options?"
    elif "price" in context.lower():
        return f"That sounds interesting. I have a budget of around ${budget}. What would you recommend?"
    else:
        return f"Hello! I'm looking for {goal}. What do you have available?"




def make_purchase_decision(conversation_context: str, retailer_message: str, shopping_goal: str, budget: float, user_id: str, session_id: str):
    """Make intelligent purchase decisions based on full conversation context."""
    import json
    import re
    
    try:
        # Parse conversation context if it's JSON
        if conversation_context.startswith('{'):
            context_data = json.loads(conversation_context)
            transaction_state = context_data.get('transaction_state', {})
            conversation_history = context_data.get('conversation_history', [])
        else:
            transaction_state = {'payment_made': False, 'payment_confirmed': False}
            conversation_history = []
    except:
        transaction_state = {'payment_made': False, 'payment_confirmed': False}
        conversation_history = []
    
    # If payment already made, handle post-payment responses
    if transaction_state.get('payment_made', False):
        if retailer_message and any(phrase in retailer_message.lower() for phrase in 
            ["payment received", "transaction confirmed", "successfully received", "thank you for your payment"]):
            return {
                'action': 'SEND_MESSAGE',
                'message': 'Thank you! The transaction is complete. Have a great day!'
            }
        elif retailer_message and "anything else" in retailer_message.lower():
            return {
                'action': 'END_CONVERSATION',
                'message': 'No, that\'s all I needed. Thank you for the smooth transaction!'
            }
        else:
            return {
                'action': 'SEND_MESSAGE',
                'message': 'I\'ve already completed the payment. Thank you!'
            }
    
    if not retailer_message:
        return {
            'action': 'SEND_MESSAGE',
            'message': f'I want to buy {shopping_goal}. Do you have it in stock? My budget is ${budget}.'
        }
    
    lower_response = retailer_message.lower()
    
    # Check if the specific product is mentioned
    goal_keywords = shopping_goal.lower().split()
    has_product = any(keyword in lower_response for keyword in goal_keywords if len(keyword) > 3)
    
    # Look for wallet address and price
    wallet_pattern = r'0x[a-fA-F0-9]{40}'
    wallet_addresses = re.findall(wallet_pattern, retailer_message)
    
    price_pattern = r'\$(\d+(?:\.\d{2})?)'
    prices = re.findall(price_pattern, retailer_message)
    
    # Also check conversation history for wallet/price
    full_context = ' '.join([str(msg) for msg in conversation_history]) + ' ' + retailer_message
    context_wallets = re.findall(wallet_pattern, full_context)
    context_prices = re.findall(price_pattern, full_context)
    
    all_wallets = wallet_addresses + context_wallets
    all_prices = prices + context_prices
    
    # Decision logic based on what information we have
    if all_wallets and all_prices:
        # We have both wallet address and price - make the payment!
        price = float(all_prices[0])
        if price <= budget:
            return {
                'action': 'MAKE_PAYMENT',
                'amount': price,
                'wallet_address': all_wallets[0],
                'reason': f'Found product {shopping_goal} for ${price}, within budget of ${budget}'
            }
        else:
            return {
                'action': 'SEND_MESSAGE',
                'message': f'${price} is over my ${budget} budget. Do you have {shopping_goal} at a lower price?'
            }
    
    elif all_wallets and not all_prices:
        # Have wallet but need price confirmation
        return {
            'action': 'SEND_MESSAGE',
            'message': f'I see your wallet address. Just to confirm, what\'s the total price for {shopping_goal}?'
        }
    
    elif has_product and ("$" in retailer_message or "price" in lower_response):
        # Product mentioned with price info
        if all_prices:
            price = float(all_prices[0])
            if price <= budget:
                return {
                    'action': 'SEND_MESSAGE',
                    'message': f'Great! I\'ll take the {shopping_goal} for ${price}. Please provide your Sepolia USDT wallet address for payment.'
                }
            else:
                return {
                    'action': 'SEND_MESSAGE',
                    'message': f'${price} is over my ${budget} budget. Do you have {shopping_goal} at a lower price?'
                }
        else:
            return {
                'action': 'SEND_MESSAGE',
                'message': f'What\'s the price for {shopping_goal}?'
            }
    
    elif "payment" in lower_response or "USDT" in lower_response or "wallet" in lower_response:
        if not all_wallets:
            return {
                'action': 'SEND_MESSAGE',
                'message': 'I can pay with USDT on Sepolia blockchain. Please provide your Sepolia wallet address.'
            }
    
    elif has_product and ("stock" in lower_response or "available" in lower_response):
        return {
            'action': 'SEND_MESSAGE',
            'message': f'Great! What\'s the price for {shopping_goal}?'
        }
    
    elif "don't have" in lower_response or "out of stock" in lower_response or "not available" in lower_response:
        return {
            'action': 'END_CONVERSATION',
            'message': 'Okay, thank you. I\'m only looking for that specific item.'
        }
    
    else:
        # Be more direct about the specific product
        return {
            'action': 'SEND_MESSAGE',
            'message': f'I specifically need {shopping_goal}. Do you have this exact product in stock?'
        }
    



