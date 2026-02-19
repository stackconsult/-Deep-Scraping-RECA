import asyncio
import os
import logging
import json
from uuid import uuid4
from datetime import datetime, UTC
from typing import Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()  # Load .env file before anything else

from core.model_router import ModelRouter
from orchestrator.orchestrator import OrchestraOrchestrator
from schemas.messages import AgentMessage, MessageType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("e2e_reca_scrape")

class MockMessageBus:
    """Mock message bus for standalone E2E testing."""
    def __init__(self, *args, **kwargs):
        self.subscribers = {}
        self.message_history = []
        self.connected = False

    async def connect(self):
        self.connected = True
        logger.info("Mock MessageBus connected")

    async def disconnect(self):
        self.connected = False
        logger.info("Mock MessageBus disconnected")

    async def subscribe_to_agent(self, agent_id: str, callback: callable):
        channel = f"agent:{agent_id}"
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        logger.info(f"Mock Subscribed to agent: {agent_id}")

    async def subscribe_to_message_type(self, message_type: MessageType, callback: callable):
        type_str = message_type.value if hasattr(message_type, 'value') else str(message_type)
        channel = f"type:{type_str}"
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        logger.info(f"Mock Subscribed to type: {type_str}")

    async def publish_message(self, message: AgentMessage):
        print(f"DEBUG: Mock Publishing {message.message_type}")
        logger.debug(f"Mock Publish: {message.message_type}")
        self.message_history.append(message)
        
        # Immediate dispatch to subscribers (simulating Redis pub/sub)
        type_str = message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type)
        channel_type = f"type:{type_str}"
        if channel_type in self.subscribers:
            for callback in self.subscribers[channel_type]:
                asyncio.create_task(callback(message))
        
        channel_agent = f"agent:{message.agent_id}"
        if channel_agent in self.subscribers:
            for callback in self.subscribers[channel_agent]:
                asyncio.create_task(callback(message))

async def run_e2e_scrape():
    """Run an end-to-end scrape using the Orchestrator and RECAScraperAgent."""
    
    # Check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if not anthropic_key and not google_key:
        logger.error("Either ANTHROPIC_API_KEY or GOOGLE_API_KEY environment variable is required")
        return

    # Initialize components
    model_router = ModelRouter()
    redis_url = "redis://mock"
    
    orchestrator = OrchestraOrchestrator(model_router, redis_url)
    
    # Inject MockMessageBus
    mock_bus = MockMessageBus()
    orchestrator.message_bus = mock_bus
    orchestrator.router.message_bus = mock_bus
    
    # Subscribe the agent to handle scrape requests via type-based channel
    async def agent_message_handler(msg: AgentMessage):
        msg_type = msg.message_type.value if hasattr(msg.message_type, 'value') else str(msg.message_type)
        print(f"DEBUG: RECAScraperAgent received message: {msg_type}")
        scrape_req_val = MessageType.SCRAPE_REQUEST.value if hasattr(MessageType.SCRAPE_REQUEST, 'value') else str(MessageType.SCRAPE_REQUEST)
        if msg_type == scrape_req_val:
            response = await orchestrator.reca_scraper.process_message(msg)
            if response:
                resp_type = response.message_type.value if hasattr(response.message_type, 'value') else str(response.message_type)
                print(f"DEBUG: RECAScraperAgent finished processing, publishing {resp_type}")
                await mock_bus.publish_message(response)

    await mock_bus.subscribe_to_message_type(MessageType.SCRAPE_REQUEST, agent_message_handler)

    try:
        # Start orchestrator
        print("Starting orchestrator with Mock MessageBus...")
        await orchestrator.start()
        
        # Create a session
        session_id = uuid4()
        print(f"Created session: {session_id}")
        
        # Manually construct a SCRAPE_REQUEST message
        scrape_message = AgentMessage(
            agent_id="e2e_tester",
            intent="start_scrape",
            message_type=MessageType.SCRAPE_REQUEST,
            payload={
                "search_params": {"last_name": "Siemens"},
                "deep_scrape": True
            },
            session_id=session_id
        )
        
        # Send through orchestrator
        print(f"Sending SCRAPE_REQUEST for session {session_id}...")
        await orchestrator.router.route_message(scrape_message)
        
        # Wait for SCRAPE_COMPLETED
        print("Waiting for scrape results...")
        max_wait = 300  # 5 minutes
        wait_time = 0
        found_results = False
        
        while wait_time < max_wait:
            for msg in mock_bus.message_history:
                if msg.message_type == MessageType.SCRAPE_COMPLETED and msg.session_id == session_id:
                    print("\n" + "="*50)
                    print("SUCCESS: Scrape completed!")
                    results = msg.payload.get("results", [])
                    print(f"Found {len(results)} results")
                    print("="*50)
                    
                    # Print first few results
                    for idx, agent in enumerate(results[:3]):
                        print(f"{idx+1}. {agent.get('name')} - {agent.get('email', 'N/A')}")
                    
                    # Save results to file
                    with open("reca_scrape_results.json", "w") as f:
                        json.dump(msg.payload, f, indent=2)
                    print(f"Results saved to reca_scrape_results.json")
                    found_results = True
                    break
            
            if found_results:
                break
                
            await asyncio.sleep(2)
            wait_time += 2
            if wait_time % 10 == 0:
                print(f"Still waiting... ({wait_time}s)")
        
        if not found_results:
            print("\n" + "!"*50)
            print("TIMEOUT: Did not receive SCRAPE_COMPLETED message")
            print("!"*50)
            
    except Exception as e:
        print(f"ERROR: E2E Scrape failed: {e}")
        logger.error(f"E2E Scrape failed: {e}", exc_info=True)
    finally:
        print("Stopping orchestrator...")
        await orchestrator.stop()
        print("Orchestrator stopped.")

if __name__ == "__main__":
    asyncio.run(run_e2e_scrape())
