
import asyncio


class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'




async def stream_text(text, prefix="", delay=0.03):
    """Stream text character by character with typing effect."""
    if prefix:
        print(prefix, end="", flush=True)
    
    for char in text:
        print(char, end="", flush=True)
        await asyncio.sleep(delay)
    print()  # New line at the end




async def print_retailer(text):
    await stream_text(text, f"\n{Colors.GREEN}🛒 Retailer: ", delay=0.02)
    print(Colors.RESET, end="")

async def print_buyer_thinking(text):
    await stream_text(text, f"{Colors.MAGENTA}🤔 Buyer thinking: ", delay=0.015)
    print(Colors.RESET, end="")

async def print_buyer_action(text):
    await stream_text(text, f"{Colors.BLUE}🤖 Buyer: ", delay=0.025)
    print(Colors.RESET, end="")

def print_system(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ Error: {text}{Colors.RESET}")
