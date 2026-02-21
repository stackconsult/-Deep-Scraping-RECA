
import asyncio
import logging
import os
from agents.deep_research_agent import DeepResearchAgent
from google_integration.gemini_client import GeminiHybridClient
from google_integration.ollama_client import OllamaHybridClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deep_research():
    print("🚀 Testing Deep Research Agent")
    print("=" * 60)
    
    # Initialize clients (mock or real depending on env)
    gemini = GeminiHybridClient()
    ollama = OllamaHybridClient()
    
    agent = DeepResearchAgent(gemini, ollama)
    
    # Test Case: Agent likely to be found via general search but maybe not direct brokerage site
    # Using a sample agent from the dataset that might be tricky
    target_agent = {
        "name": "Kirtis Siemens",  # Using a known entity or a real agent
        "first_name": "Kirtis",
        "last_name": "Siemens",
        "brokerage": "StackConsult",
        "city": "Edmonton"
    }
    
    # Alternatively, use a real agent from our failures list if we want to stress test
    # target_agent = {
    #     "name": "Miladin Peric", 
    #     "brokerage": "HOMES & GARDENS REAL ESTATE LIMITED",
    #     "city": "Edmonton"
    # }
    
    print(f"Target: {target_agent['name']} at {target_agent['brokerage']}")
    
    try:
        result = await agent.execute(target_agent)
        
        print("\n📊 Results:")
        print(f"Emails: {result.get('emails')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Sources: {result.get('sources')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_deep_research())
