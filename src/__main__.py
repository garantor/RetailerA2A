# __ main.py usually contains the main entry point agent.

import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from dotenv import load_dotenv
load_dotenv()

from agent_executor import (
    RetailerAgentExecutor,
)

from agent import Retailer_Root_Agent

if __name__ == '__main__':
    # Skills for the retailer agent
    inventory_skill = AgentSkill(
        id='inventory_management',
        name='Inventory Management',
        description='Check inventory, search for products, and view stock levels for electronics store.',
        tags=['inventory', 'products', 'stock', 'electronics'],
        examples=['show me inventory', 'search for headphones', 'what products do you have'],
    )
    
    payment_skill = AgentSkill(
        id='usdc_payment_processing',
        name='USDC Payment Processing',
        description='Handle USDC cryptocurrency payments on Ethereum, Polygon, and Arbitrum networks. Provide wallet addresses and verify transactions.',
        tags=['payment', 'USDC', 'blockchain', 'cryptocurrency', 'ethereum', 'polygon', 'arbitrum'],
        examples=['how can I pay?', 'payment info for polygon', 'verify my transaction', 'supported payment methods'],
    )
    
    memory_skill = AgentSkill(
        id='conversation_memory',
        name='Conversation Memory',
        description='Remember customer preferences, previous conversations, and maintain session continuity across interactions.',
        tags=['memory', 'preferences', 'history', 'personalization'],
        examples=['what did we discuss before?', 'remember my preferences', 'show conversation history'],
    )

    # Public agent card
    public_agent_card = AgentCard(
        name='Crypto Electronics Retailer',
        description='An intelligent electronics retail agent that manages inventory, processes USDC payments on multiple blockchain networks, and remembers your preferences across conversations.',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[inventory_skill, payment_skill],  # Basic skills for public
        supportsAuthenticatedExtendedCard=True,
    )

    # Extended agent card with full capabilities
    specific_extended_agent_card = public_agent_card.model_copy(
        update={
            'name': 'Crypto Electronics Retailer - Premium',
            'description': 'Full-featured electronics retail agent with advanced memory capabilities, comprehensive USDC payment processing, and personalized shopping experience.',
            'version': '1.1.0',
            'skills': [
                inventory_skill,
                payment_skill,
                memory_skill,  # Extended memory features
            ],
        }
    )

    request_handler = DefaultRequestHandler(
        agent_executor=RetailerAgentExecutor(
            agent=Retailer_Root_Agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)