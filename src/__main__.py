
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

from agent import  Retailer_Root_Agent

if __name__ == '__main__':
    # --8<-- [start:AgentSkill]
    skill = AgentSkill(
        id='Retailer_Agent',
        name='get_inventory',
        description='This is a simple retialer agent that return the list of inventory items, they have in stock.',
        tags=['Retailer', 'Inventory', 'Store'],
        # examples=['hi', 'hello world'],
    )
    # --8<-- [end:AgentSkill]

    # extended_skill = AgentSkill(
    #     id='super_hello_world',
    #     name='Returns a SUPER Hello World',
    #     description='A more enthusiastic greeting, only for authenticated users.',
    #     tags=['hello world', 'super', 'extended'],
    #     examples=['super hi', 'give me a super hello'],
    # )

    # --8<-- [start:AgentCard]
    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='Agentic Store',
        description='A simple agent that returns a list of inventory items.',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],  # Only the basic skill for the public card
        supportsAuthenticatedExtendedCard=True,
    )
    # --8<-- [end:AgentCard]

    # This will be the authenticated extended agent card
    # It includes the additional 'extended_skill'
    specific_extended_agent_card = public_agent_card.model_copy(
        update={
            'name': 'Hello World Agent - Extended Edition',  # Different name for clarity
            'description': 'The full-featured hello world agent for authenticated users.',
            'version': '1.0.1',  # Could even be a different version
            # Capabilities and other fields like url, defaultInputModes, defaultOutputModes,
            # supportsAuthenticatedExtendedCard are inherited from public_agent_card unless specified here.
            'skills': [
                skill,
                # extended_skill,
            ],  # Both skills for the extended card
        }
    )

    request_handler = DefaultRequestHandler(
        agent_executor=RetailerAgentExecutor(
            agent= Retailer_Root_Agent,

        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)