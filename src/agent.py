from google.adk.agents import Agent
from google.adk.tools import google_search, FunctionTool

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

def get_inventory():
    """Return the current inventory items."""
    return INVENTORY_ITEMS

# @tool
def check_inventory():
    """Get current inventory with all items, prices, and stock levels."""
    items = get_inventory()
    inventory_text = "📦 **Current Inventory:**\n\n"
    for item in items:
        inventory_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
    return inventory_text

# @tool
def search_product(product_name: str):
    """Search for a specific product in inventory by name."""
    items = get_inventory()
    results = [item for item in items if product_name.lower() in item['name'].lower()]
    
    if not results:
        return f"❌ No products found matching '{product_name}'"
    
    result_text = f"🔍 **Found {len(results)} product(s) matching '{product_name}':**\n\n"
    for item in results:
        result_text += f"• **{item['name']}** - ${item['price']:.2f} (Stock: {item['stock']})\n"
    return result_text



check_tool = FunctionTool(func=check_inventory)
serach_tool = FunctionTool(func=search_product)

tool_List = [check_tool, serach_tool]
Retailer_Root_Agent = Agent(
    name="retailer_agent",
    model="gemini-2.5-flash-lite-preview-06-17",
    description="Agent to handle retail-related queries and provide information about inventory.",
    instruction=(
        "You are a Retailer Agent for an electronics retail store. "
        "Use the available tools to help customers with inventory inquiries:\n"
        "- Use 'check_inventory' to show all available products\n"
        "- Use 'search_product' to find specific items\n"
        "Always be helpful and provide accurate pricing and stock information."
    ),
    tools= tool_List,
)