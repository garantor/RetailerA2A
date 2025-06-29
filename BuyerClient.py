import asyncio
import httpx
from uuid import uuid4
import json
import os
from datetime import datetime

from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, Message, TextPart, AgentCard, Role, Task, JSONRPCError, SendMessageResponse

AGENT_BASE_URL = "http://0.0.0.0:9999"
USER_SESSION_FILE = "user_session.json"

# ANSI color codes
class Colors:
    GREEN = '\033[92m'      # Bright green for agent responses
    BLUE = '\033[94m'       # Blue for system messages
    YELLOW = '\033[93m'     # Yellow for status/info
    RED = '\033[91m'        # Red for errors
    BOLD = '\033[1m'        # Bold text
    RESET = '\033[0m'       # Reset to normal

def print_agent(text):
    """Print agent response in green."""
    print(f"\n{Colors.GREEN}Agent: {text}{Colors.RESET}")

def print_user(text):
    """Print user input in normal color."""
    print(f"You: {text}")

def print_system(text):
    """Print system messages in blue."""
    print(f"{Colors.BLUE}{text}{Colors.RESET}")

def print_status(text):
    """Print status messages in yellow."""
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")

def print_error(text):
    """Print error messages in red."""
    print(f"{Colors.RED}Error: {text}{Colors.RESET}")

class PersistentBuyerClient:
    def __init__(self):
        self.user_id = None
        self.session_id = None
        self.load_or_create_session()
    
    def load_or_create_session(self):
        """Load existing session or create new one."""
        if os.path.exists(USER_SESSION_FILE):
            try:
                with open(USER_SESSION_FILE, 'r') as f:
                    session_data = json.load(f)
                    self.user_id = session_data.get('user_id')
                    self.session_id = session_data.get('session_id')
                    print_system(f"Loaded existing session - User: {self.user_id}, Session: {self.session_id}")
                    return
            except Exception as e:
                print_error(f"Error loading session: {e}")
        
        # Create new session
        self.create_new_session()
    
    def create_new_session(self):
        """Create a new user session."""
        timestamp = int(datetime.now().timestamp())
        self.user_id = input("Enter your user ID (or press Enter for auto-generated): ").strip()
        
        if not self.user_id:
            self.user_id = f"buyer_{timestamp}_{uuid4().hex[:8]}"
        
        self.session_id = f"{self.user_id}_session_{timestamp}"
        
        # Save session
        session_data = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': datetime.now().isoformat()
        }
        
        with open(USER_SESSION_FILE, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print_system(f"Created new session - User: {self.user_id}, Session: {self.session_id}")
    
    def get_headers(self):
        """Get headers with user identification."""
        return {
            'X-User-ID': self.user_id,
            'X-Session-ID': self.session_id,
            'Content-Type': 'application/json'
        }

async def run_client():
    # Initialize persistent client
    buyer_client = PersistentBuyerClient()
    
    # Custom headers for user identification
    headers = buyer_client.get_headers()
    
    async with httpx.AsyncClient(headers=headers) as httpx_client:
        try:
            # 1. Fetch the Agent Card explicitly
            agent_card_url = f"{AGENT_BASE_URL}/.well-known/agent.json"
            print_status(f"Attempting to fetch Agent Card from: {agent_card_url}")
            agent_card_response = await httpx_client.get(agent_card_url)
            agent_card_response.raise_for_status()

            agent_card_data = agent_card_response.json()
            agent_card = AgentCard(**agent_card_data)

            print_system(f"Connected to agent: {agent_card.name}")
            print_system(f"Agent description: {agent_card.description}")
            print_system(f"Session Info: User={buyer_client.user_id}, Session={buyer_client.session_id}\n")

            client = A2AClient(httpx_client=httpx_client, url=AGENT_BASE_URL)

            while True:
                user_input = input(f"\n{Colors.RESET}You: ")
                
                if user_input.lower() in ["exit", "quit"]:
                    print_system("Exiting client.")
                    break
                elif user_input.lower() == "new session":
                    buyer_client.create_new_session()
                    # Update headers with new session info
                    httpx_client.headers.update(buyer_client.get_headers())
                    print_system("Started new session!")
                    continue
                elif user_input.lower() == "session info":
                    print_system(f"Current User: {buyer_client.user_id}")
                    print_system(f"Current Session: {buyer_client.session_id}")
                    continue

                # 2. Prepare the message payload with user context
                message_id_hex = uuid4().hex
                
                # Use session-based task ID for continuity
                task_id = f"{buyer_client.session_id}_{message_id_hex[:8]}"

                # Enhanced user message with identity context
                enhanced_input = f"[User: {buyer_client.user_id}] {user_input}"
                
                user_message = Message(
                    messageId=message_id_hex,
                    role=Role.user,
                    parts=[TextPart(text=enhanced_input)]
                )

                request = SendMessageRequest(
                    id=task_id,
                    params=MessageSendParams(
                        message=user_message,
                    )
                )

                # print_status("Sending request...")
                response = await client.send_message(request)

                # Extract the task from the nested response structure
                task_object = None
                
                try:
                    # Handle nested response structure: response.root.result
                    if hasattr(response, 'root') and hasattr(response.root, 'result'):
                        task_object = response.root.result
                    elif hasattr(response, 'result'):
                        task_object = response.result
                    elif isinstance(response, Task):
                        task_object = response
                    else:
                        print_error(f"Unexpected response structure: {type(response)}")
                        continue
                        
                except Exception as e:
                    print_error(f"Error extracting task from response: {e}")
                    continue

                # Verify we have a Task object
                if not isinstance(task_object, Task):
                    print_error(f"Expected a Task object, but got {type(task_object)}")
                    continue

                task_status = task_object.status.state
                # print_status(f"Task Status: {task_status}")

                if task_status.value == "completed":  # Use .value for enum comparison
                    agent_reply = None
                    
                    # First, try to get response from artifacts
                    if task_object.artifacts:
                        for artifact in task_object.artifacts:
                            if artifact.name == "response" and artifact.parts:
                                for part in artifact.parts:
                                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                        agent_reply = part.root.text
                                        break
                                if agent_reply:
                                    break
                    
                    # If no artifact response, check messages
                    if not agent_reply and task_object.history:
                        for msg in reversed(task_object.history):
                            if msg.role == Role.agent and msg.parts:
                                for part in msg.parts:
                                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                        text = part.root.text
                                        # Skip "Processing request..." messages
                                        if text and text.strip() != "Processing request...":
                                            agent_reply = text
                                            break
                                if agent_reply:
                                    break
                        
                    if agent_reply:
                        print_agent(agent_reply.strip())
                    else:
                        print_error("Agent completed task, but no text response found.")
                        # Debug info
                        print_status(f"Available artifacts: {[art.name for art in task_object.artifacts] if task_object.artifacts else 'None'}")
                        print_status(f"Available messages: {len(task_object.history) if task_object.history else 0}")

                elif task_status.value == "working":
                    print_status("Agent is still working...")
                elif task_status.value == "failed":
                    error_message = "Unknown error."
                    if hasattr(task_object, 'error') and task_object.error:
                        error_message = task_object.error.message
                    print_error(f"Agent failed: {error_message}")
                else:
                    print_status(f"Unknown task status: {task_status}")

        except httpx.HTTPStatusError as e:
            print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print_error(f"Network Error: {e}")
        except Exception as e:
            print_error(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print(f"{Colors.BOLD}Retailer A2A Buyer Client{Colors.RESET}")
    print_system("Commands: 'new session', 'session info', 'exit', 'quit'")
    print_system("-" * 50)
    asyncio.run(run_client())