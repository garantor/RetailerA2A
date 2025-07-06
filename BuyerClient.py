import asyncio
import httpx
from uuid import uuid4
import json
import re
import os
from datetime import datetime
# ...existing code...
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, Message, TextPart, AgentCard, Role, Task
from dotenv import load_dotenv

from web3 import Web3
from eth_account import Account

from Tools.blockchain import get_wallet_info, send_USDT_payment, check_payment_status
from Tools.buyer import analyze_retailer_response, make_purchase_decision, update_shopping_context, generate_buyer_response
from Tools.shipping import get_shipping_address, get_tracking_info, update_shipping_status
from Tools.utils import Colors, print_system, print_buyer_thinking, print_error, print_buyer_action, print_retailer, stream_text
from Tools.decide_next_action import decide_next_action

load_dotenv()

AGENT_BASE_URL = "http://0.0.0.0:9999"


# Create payment tool instances
payment_tool = FunctionTool(func=send_USDT_payment)
payment_status_tool = FunctionTool(func=check_payment_status)
wallet_info_tool = FunctionTool(func=get_wallet_info)
# Create tool instances
analyze_tool = FunctionTool(func=analyze_retailer_response)
decision_tool = FunctionTool(func=make_purchase_decision)
context_tool = FunctionTool(func=update_shopping_context)
response_tool = FunctionTool(func=generate_buyer_response)
action_tool = FunctionTool(func=decide_next_action)

# Create shipping tool instances
shipping_address_tool = FunctionTool(func=get_shipping_address)
shipping_status_tool = FunctionTool(func=update_shipping_status)
tracking_info_tool = FunctionTool(func=get_tracking_info)




# Create the Buyer Agent

# Create the Buyer Agent
Buyer_Agent = Agent(
    name="autonomous_buyer_agent",
    model="gemini-2.5-flash-lite-preview-06-17",
    description="Direct AI buyer agent that purchases specific products efficiently using USDT on Sepolia.",
    instruction=(
        "You are a direct, efficient AI buyer agent. Your ONLY job is to buy the EXACT product specified in your shopping goal using USDT payments on Sepolia blockchain.\n\n"
        "Rules:\n"
        "- Be direct and to the point\n"
        "- Only ask about the SPECIFIC product in your goal\n"
        "- Don't browse or ask about other products\n"
        "- If they don't have your product, end the conversation\n"
        "- If they have it and it's within budget, buy it immediately with USDT\n"
        "- Don't ask unnecessary questions\n"
        "- Focus only on: availability, price, and USDT payment on Sepolia\n"
        "- Always check wallet balance before making payments\n"
        "- Confirm payment transactions and provide transaction hashes\n"
        "- After payment confirmation, provide shipping address for delivery\n\n"
        
        "Your conversation flow:\n"
        "1. Ask if they have the specific product\n"
        "2. Ask for the price\n"
        "3. If affordable, ask for their Sepolia USDT wallet address\n"
        "4. Send USDT payment on Sepolia blockchain\n"
        "5. Provide transaction confirmation\n"
        "6. When retailer confirms payment, provide shipping address\n"
        "7. Track shipping status if needed\n\n"
        "Be efficient and decisive. Only use USDT on Sepolia for payments."
    ),
    tools=[analyze_tool, decision_tool, context_tool, response_tool, action_tool, 
           payment_tool, payment_status_tool, wallet_info_tool,
           shipping_address_tool, shipping_status_tool, tracking_info_tool],
)
class AutonomousBuyerAgent:
    def __init__(self, shopping_goal="Browse products and make a purchase if something interesting is available"):
        self.user_id = f"ai_buyer_{int(datetime.now().timestamp())}_{uuid4().hex[:6]}"
        self.session_id = f"{self.user_id}_session"
        self.shopping_goal = shopping_goal
        self.conversation_history = []
        self.budget = 500  # More flexible default budget
        self.purchased_items = []
        self.agent = Buyer_Agent
        
        print_system(f"AI Buyer Agent initialized: {self.user_id}")
        print_system(f"Goal: {self.shopping_goal}")
        print_system(f"Budget: ${self.budget}")
    
    def get_headers(self):
        return {
            'X-User-ID': self.user_id,
            'X-Session-ID': self.session_id,
            'Content-Type': 'application/json'
        }

    async def think_and_decide(self, retailer_response=None):
        """Use logic to decide what to say next and execute payment if needed."""
        try:
            # Show thinking indicator
            await print_buyer_thinking("Analyzing situation and deciding next move...")
            
            # Use the decision tool directly
            current_context = "\n".join(self.conversation_history[-3:]) if self.conversation_history else ""
            
            decision = decide_next_action(
                current_context=current_context,
                retailer_response=retailer_response or "",
                shopping_goal=self.shopping_goal,
                budget=self.budget,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # Check if this decision involves providing shipping address
            if decision.startswith("PROVIDE_SHIPPING_ADDRESS:"):
                # Extract transaction hash from the decision
                transaction_hash = decision.replace("PROVIDE_SHIPPING_ADDRESS:", "").strip()
                
                await print_buyer_thinking(f"Providing shipping address for transaction: {transaction_hash}")
                
                # Call the shipping address function
                shipping_result = get_shipping_address(
                    payment_confirmed=True,
                    transaction_hash=transaction_hash,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                
                await print_buyer_thinking(f"Shipping address generated: {shipping_result}")
                return shipping_result
            
            # Check if this decision involves making a payment
            elif decision.startswith("EXECUTE_PAYMENT:"):
                # Extract payment details from the decision
                payment_text = decision.replace("EXECUTE_PAYMENT:", "")
                price_match = re.search(r'\$(\d+(?:\.\d{2})?)', payment_text)
                wallet_match = re.search(r'0x[a-fA-F0-9]{40}', payment_text)
                
                if price_match and wallet_match:
                    price = float(price_match.group(1))
                    wallet_address = wallet_match.group(0)
                    
                    await print_buyer_thinking(f"Executing USDT payment: ${price} to {wallet_address}")
                    print_system("Processing blockchain transaction... This may take up to 5 minutes.")
                    
                    # Actually call the payment function and wait for result
                    payment_result = send_USDT_payment(
                        recipient_address=wallet_address,
                        amount=price,
                        user_id=self.user_id,
                        session_id=self.session_id
                    )
                    
                    await print_buyer_thinking(f"Payment result: {payment_result}")
                    
                    # Return the actual payment result
                    return payment_result
            
            await print_buyer_thinking(f"Decided to say: '{decision}'")
            return decision
            
        except Exception as e:
            print_error(f"Decision making failed: {e}")
            return f"Hello! I'm looking for {self.shopping_goal}. What products do you have available? (User: {self.user_id}, Session: {self.session_id})"
   
    async def send_message_to_retailer(self, client, message):
        """Send message to retailer agent and get response."""
        # Show sending indicator
        await stream_text("Sending message to retailer...", f"{Colors.YELLOW}📤 ", delay=0.01)
        print(Colors.RESET, end="")
        
        message_id = uuid4().hex
        task_id = f"{self.session_id}_{message_id[:8]}"
        
        user_message = Message(
            messageId=message_id,
            role=Role.user,
            parts=[TextPart(text=message)]
        )

        request = SendMessageRequest(
            id=task_id,
            params=MessageSendParams(message=user_message)
        )

        response = await client.send_message(request)
        
        # Show processing indicator
        await stream_text("Waiting for retailer response...", f"{Colors.YELLOW}⏳ ", delay=0.01)
        print(Colors.RESET, end="")
        
        # Extract task from response
        task_object = None
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task_object = response.root.result
        elif hasattr(response, 'result'):
            task_object = response.result
        elif isinstance(response, Task):
            task_object = response

        if not isinstance(task_object, Task):
            return "Error: Invalid response from retailer"

        # Get retailer's reply
        if task_object.status.state.value == "completed":
            # Try artifacts first
            if task_object.artifacts:
                for artifact in task_object.artifacts:
                    if artifact.name == "response" and artifact.parts:
                        for part in artifact.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                return part.root.text
            
            # Try message history
            if task_object.history:
                for msg in reversed(task_object.history):
                    if msg.role == Role.agent and msg.parts:
                        for part in msg.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                text = part.root.text
                                if text and text.strip() != "Processing request...":
                                    return text
            
            return "Retailer completed but no response found"
        
        elif task_object.status.state.value == "failed":
            error_msg = task_object.error.message if hasattr(task_object, 'error') and task_object.error else "Unknown error"
            return f"Retailer failed: {error_msg}"
        
        return "Retailer is processing..."

    async def autonomous_shopping_session(self, client, max_interactions=10):
        """Run an autonomous shopping session."""
        print_system("🚀 Starting autonomous shopping session...")
        
        # Start the conversation
        initial_message = await self.think_and_decide()
        retailer_response = None
        
        for interaction in range(max_interactions):
            print_system(f"\n--- Interaction {interaction + 1} ---")
            
            # Decide what to say
            if interaction == 0:
                buyer_message = initial_message
            else:
                buyer_message = await self.think_and_decide(retailer_response)
            
            await print_buyer_action(buyer_message)
            self.conversation_history.append(f"Buyer: {buyer_message}")
            
            # Send to retailer
            try:
                retailer_response = await self.send_message_to_retailer(client, buyer_message)
                await print_retailer(retailer_response)
                self.conversation_history.append(f"Retailer: {retailer_response}")
                
                # Check if conversation should end
                if any(phrase in buyer_message.lower() for phrase in ["goodbye", "thank you", "that's all", "bye"]):
                    print_system("Buyer decided to end the conversation")
                    break
                    
                # Add delay to be polite
                await stream_text("Contemplating next move...", f"{Colors.YELLOW}💭 ", delay=0.01)
                print(Colors.RESET, end="")
                await asyncio.sleep(1)
                
            except Exception as e:
                print_error(f"Failed to communicate with retailer: {e}")
                break
        
        print_system("🏁 Shopping session completed!")
        print_system(f"Purchased items: {self.purchased_items if self.purchased_items else 'None'}")

async def main():
    await stream_text("Autonomous AI Buyer Agent (Powered by Agent SDK)", f"{Colors.BOLD}🤖 ", delay=0.05)
    print(Colors.RESET, end="")
    print_system("This AI agent will autonomously shop and make purchases!")
    
    goal = input("\nWhat should the AI buyer's goal be? (or press Enter for default): ").strip()
    if not goal:
        goal = "Browse available products and make a purchase within budget"
    
    try:
        buyer = AutonomousBuyerAgent(shopping_goal=goal)
        
        async with httpx.AsyncClient(headers=buyer.get_headers()) as httpx_client:
            # Connect to retailer agent
            await stream_text("Connecting to retailer agent...", f"{Colors.YELLOW}🔗 ", delay=0.01)
            print(Colors.RESET, end="")
            
            agent_card_response = await httpx_client.get(f"{AGENT_BASE_URL}/.well-known/agent.json")
            agent_card_response.raise_for_status()
            
            agent_card = AgentCard(**agent_card_response.json())
            print_system(f"Connected to retailer: {agent_card.name}")
            
            client = A2AClient(httpx_client=httpx_client, url=AGENT_BASE_URL)
            
            # Run autonomous shopping
            await buyer.autonomous_shopping_session(client)
            
    except Exception as e:
        print_error(f"Failed to initialize: {e}")

if __name__ == "__main__":
    asyncio.run(main())