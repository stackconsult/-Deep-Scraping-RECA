import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from mem0 import MemoryClient
except ImportError:
    MemoryClient = None

logger = logging.getLogger(__name__)

class Mem0MemoryManager:
    """Manager for Mem0 persistent memory interactions"""
    
    def __init__(self):
        self.api_key = os.getenv("MEM0_API_KEY")
        if not self.api_key:
            logger.warning("MEM0_API_KEY not found. Memory features will be disabled.")
            self.client = None
        elif MemoryClient:
            try:
                self.client = MemoryClient(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 client: {e}")
                self.client = None
        else:
            logger.warning("mem0ai package not installed. Memory features will be disabled.")
            self.client = None
            
        self.user_id = "email_extractor_agent"
        
    async def add_skill(self, skill_name: str, pattern: str, brokerage_type: str, confidence: float, success_count: int):
        """Add a learned skill/pattern to memory"""
        if not self.client:
            return
            
        try:
            content = f"Learned Pattern: {pattern} for {brokerage_type}"
            metadata = {
                "type": "skill",
                "skill_name": skill_name,
                "pattern": pattern,
                "brokerage_type": brokerage_type,
                "confidence": confidence,
                "success_count": success_count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to memory
            self.client.add(content, user_id=self.user_id, metadata=metadata)
            logger.info(f"Added skill to memory: {skill_name}")
            
        except Exception as e:
            logger.error(f"Failed to add skill to memory: {e}")

    async def get_agent_history(self, agent_id: str) -> List[Dict]:
        """Get processing history for a specific agent"""
        if not self.client:
            return []
            
        try:
            # Search for touch points related to this agent
            query = f"history for agent {agent_id}"
            results = self.client.search(
                query, 
                user_id=self.user_id, 
                filters={"type": "touch_point", "agent_id": agent_id},
                limit=5
            )
            
            history = []
            for result in results:
                if 'metadata' in result:
                    history.append(result['metadata'])
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get agent history: {e}")
            return []

    async def add_touch_point(self, agent_id: str, agent_data: Dict, extraction_result: Dict, strategy: Dict):
        """Record a processing touch point"""
        if not self.client:
            return
            
        try:
            content = f"Processed agent {agent_id}: {agent_data.get('name')}"
            metadata = {
                "type": "touch_point",
                "agent_id": agent_id,
                "agent_name": agent_data.get('name'),
                "brokerage": agent_data.get('brokerage'),
                "extraction_result": extraction_result,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat()
            }
            
            self.client.add(content, user_id=self.user_id, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Failed to add touch point: {e}")

    def get_memory_stats(self) -> Dict:
        """Get memory connection statistics"""
        return {
            "enabled": self.client is not None,
            "user_id": self.user_id
        }
