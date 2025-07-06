import random
from typing import Optional


# Dummy shipping addresses for simulation
DUMMY_ADDRESSES = [
    {
        "name": "John Smith",
        "address": "123 Main Street, Apt 4B",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94102",
        "country": "USA",
        "phone": "+1-555-0123"
    },
    # {
    #     "name": "Sarah Johnson", 
    #     "address": "456 Oak Avenue, Suite 200",
    #     "city": "New York",
    #     "state": "NY", 
    #     "zip": "10001",
    #     "country": "USA",
    #     "phone": "+1-555-0456"
    # },
    # {
    #     "name": "Mike Chen",
    #     "address": "789 Pine Road, Unit 15",
    #     "city": "Seattle",
    #     "state": "WA",
    #     "zip": "98101", 
    #     "country": "USA",
    #     "phone": "+1-555-0789"
    # },
    # {
    #     "name": "Emily Davis",
    #     "address": "321 Elm Street, Floor 3",
    #     "city": "Austin",
    #     "state": "TX",
    #     "zip": "73301",
    #     "country": "USA", 
    #     "phone": "+1-555-0321"
    # }
]


def get_shipping_address(payment_confirmed: bool, transaction_hash: str, user_id: str, session_id: str) -> str:
    """
    Provide shipping address when payment has been confirmed by retailer.
    
    Args:
        payment_confirmed: Whether payment has been confirmed by retailer
        transaction_hash: The blockchain transaction hash for verification
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Formatted shipping address or error message
    """
    
    if not payment_confirmed:
        return "❌ Cannot provide shipping address: Payment not yet confirmed by retailer. Please wait for payment confirmation."
    
    if not transaction_hash or len(transaction_hash) < 10:
        return "❌ Cannot provide shipping address: Invalid or missing transaction hash. Please provide valid transaction hash."
    
    try:
        # Use transaction hash to deterministically select address (for consistency)
        hash_sum = sum(ord(c) for c in transaction_hash[-8:])
        selected_address = DUMMY_ADDRESSES[hash_sum % len(DUMMY_ADDRESSES)]
        
        # Format the shipping address
        formatted_address = (
            f"📦 SHIPPING ADDRESS CONFIRMED:\n"
            f"📍 Name: {selected_address['name']}\n"
            f"🏠 Address: {selected_address['address']}\n"
            f"🏙️  City: {selected_address['city']}, {selected_address['state']} {selected_address['zip']}\n"
            f"🌍 Country: {selected_address['country']}\n"
            f"📞 Phone: {selected_address['phone']}\n"
            f"🔗 Transaction: {transaction_hash}\n"
            f"✅ Shipping will be processed within 24-48 hours"
        )
        
        return formatted_address
        
    except Exception as e:
        return f"❌ Error generating shipping address: {str(e)}"


def update_shipping_status(transaction_hash: str, status: str, user_id: str, session_id: str) -> str:
    """
    Update shipping status for a confirmed payment.
    
    Args:
        transaction_hash: The blockchain transaction hash
        status: New shipping status (processing, shipped, delivered, etc.)
        user_id: User identifier  
        session_id: Session identifier
        
    Returns:
        Status update message
    """
    
    valid_statuses = ["processing", "shipped", "in_transit", "delivered", "cancelled"]
    
    if status.lower() not in valid_statuses:
        return f"❌ Invalid status: {status}. Valid statuses: {', '.join(valid_statuses)}"
    
    if not transaction_hash:
        return "❌ Transaction hash required for status update"
    
    try:
        status_messages = {
            "processing": "📦 Your order is being processed and will ship within 24-48 hours",
            "shipped": "🚚 Your order has been shipped! Tracking information will be provided soon",
            "in_transit": "🛣️  Your order is in transit and on its way to you",
            "delivered": "✅ Your order has been delivered successfully!",
            "cancelled": "❌ Your order has been cancelled and refund is being processed"
        }
        
        return f"🔄 SHIPPING UPDATE:\n{status_messages[status.lower()]}\nTransaction: {transaction_hash}"
        
    except Exception as e:
        return f"❌ Error updating shipping status: {str(e)}"


def get_tracking_info(transaction_hash: str, user_id: str, session_id: str) -> str:
    """
    Get tracking information for a shipped order.
    
    Args:
        transaction_hash: The blockchain transaction hash
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Tracking information or error message
    """
    
    if not transaction_hash:
        return "❌ Transaction hash required for tracking lookup"
    
    try:
        # Generate dummy tracking number based on transaction hash
        hash_suffix = transaction_hash[-8:] if len(transaction_hash) >= 8 else transaction_hash
        tracking_number = f"TRK{hash_suffix.upper()}"
        
        # Generate dummy carrier
        carriers = ["FedEx", "UPS", "DHL", "USPS"]
        hash_sum = sum(ord(c) for c in transaction_hash[-4:])
        carrier = carriers[hash_sum % len(carriers)]
        
        # Generate estimated delivery
        import datetime
        delivery_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(2, 7))
        
        tracking_info = (
            f"📋 TRACKING INFORMATION:\n"
            f"📦 Tracking Number: {tracking_number}\n"
            f"🚚 Carrier: {carrier}\n"
            f"📅 Estimated Delivery: {delivery_date.strftime('%B %d, %Y')}\n"
            f"🔗 Transaction: {transaction_hash}\n"
            f"📱 Track online at: https://track.{carrier.lower()}.com/{tracking_number}"
        )
        
        return tracking_info
        
    except Exception as e:
        return f"❌ Error retrieving tracking information: {str(e)}"