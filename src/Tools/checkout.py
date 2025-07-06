import random
import string
from Tools.memory import conversation_memory
from datetime import datetime, timedelta



def generate_tracking_id():
    """Generate a dummy tracking ID."""
    prefix = "TRK"
    numbers = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{numbers}"

def generate_order_id():
    """Generate a dummy order ID."""
    prefix = "ORD"
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{numbers}"

def checkout_order(items: str, total_amount: float, shipping_address: str, user_id: str, session_id: str):
    """Process checkout with shipping address and generate order confirmation."""
    actual_session_id = conversation_memory.get_or_create_session_for_user(user_id, session_id)
    
    # Generate order and tracking IDs
    order_id = generate_order_id()
    tracking_id = generate_tracking_id()
    
    # Estimate delivery date (3-7 business days)
    delivery_days = random.randint(3, 7)
    delivery_date = (datetime.now() + timedelta(days=delivery_days)).strftime("%B %d, %Y")
    
    checkout_text = f"🛒 **Order Confirmation**\n\n"
    checkout_text += f"**Order ID:** {order_id}\n"
    checkout_text += f"**Tracking ID:** {tracking_id}\n\n"
    
    checkout_text += f"**Order Summary:**\n"
    checkout_text += f"Items: {items}\n"
    checkout_text += f"Total Amount: ${total_amount:.2f} USDT\n\n"
    
    checkout_text += f"**Shipping Information:**\n"
    checkout_text += f"📍 **Delivery Address:**\n{shipping_address}\n\n"
    
    checkout_text += f"**Delivery Details:**\n"
    checkout_text += f"• Estimated Delivery: {delivery_date}\n"
    checkout_text += f"• Shipping Method: Standard Delivery (3-7 business days)\n"
    checkout_text += f"• Carrier: RetailExpress\n\n"
    
    checkout_text += f"**Next Steps:**\n"
    checkout_text += f"1. ✅ Your order has been confirmed\n"
    checkout_text += f"2. 📦 Items will be packed within 24 hours\n"
    checkout_text += f"3. 🚚 You'll receive shipping notification with tracking link\n"
    checkout_text += f"4. 📱 Track your package using: {tracking_id}\n\n"
    
    checkout_text += f"**Important Notes:**\n"
    checkout_text += f"• Please ensure USDT payment is completed before shipping\n"
    checkout_text += f"• Contact support if you need to modify your order\n"
    checkout_text += f"• Keep your tracking ID for package updates\n\n"
    
    checkout_text += f"Thank you for shopping with us! 🎉"
    
    # Store checkout information in memory
    checkout_data = {
        "timestamp": datetime.now().isoformat(),
        "order_id": order_id,
        "tracking_id": tracking_id,
        "items": items,
        "total_amount": total_amount,
        "shipping_address": shipping_address,
        "estimated_delivery": delivery_date,
        "status": "confirmed",
        "user_id": user_id
    }
    
    # Add to session memory
    if actual_session_id not in conversation_memory.memory:
        conversation_memory.memory[actual_session_id] = {
            "conversation_history": [],
            "user_preferences": {},
            "past_searches": [],
            "payment_requests": [],
            "orders": [],
            "created_at": datetime.now().isoformat()
        }
    
    if "orders" not in conversation_memory.memory[actual_session_id]:
        conversation_memory.memory[actual_session_id]["orders"] = []
    
    conversation_memory.memory[actual_session_id]["orders"].append(checkout_data)
    conversation_memory._save_memory()
    
    # Update conversation memory
    conversation_memory.update_session_memory(
        actual_session_id,
        f"checkout_order: {items} - ${total_amount}",
        checkout_text,
        {"action": "checkout", "order_id": order_id, "tracking_id": tracking_id, "total": total_amount}
    )
    
    return checkout_text