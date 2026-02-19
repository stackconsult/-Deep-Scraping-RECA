import logging
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID

from core.model_router import ModelRouter
from schemas.messages import AgentMessage, MessageType
from integrations.reca_scraper_logic import RECAHttpScraper

logger = logging.getLogger(__name__)

class RECAScraperAgent:
    def __init__(self, model_router: ModelRouter):
        self.router = model_router
        self.agent_id = "reca_scraper"
        self.scraper = RECAHttpScraper()

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Processes scraping requests.
        """
        if message.message_type == MessageType.SCRAPE_REQUEST:
            return await self._handle_scrape_request(message)
        return None

    async def _handle_scrape_request(self, message: AgentMessage) -> AgentMessage:
        """
        Executes the scraping process based on the search criteria in the message content.
        """
        session_id = message.session_id
        search_params = message.payload.get("search_params", {})
        last_name = search_params.get("last_name")

        if not last_name:
            return AgentMessage(
                agent_id=self.agent_id,
                intent="error_occurred",
                message_type=MessageType.ERROR_OCCURRED,
                payload={"error": "Missing 'last_name' in search parameters."},
                session_id=session_id
            )

        logger.info(f"Agent {self.name if hasattr(self, 'name') else self.agent_id} starting scrape for last name: {last_name}")
        
        try:
            # Reusing the HTTP scraper logic
            results = self.scraper.search_by_lastname(last_name)
            
            # Optionally, perform deep scraping for each result if requested
            if message.payload.get("deep_scrape", False):
                results = await self._perform_deep_scrape(session_id, results)

            return AgentMessage(
                agent_id=self.agent_id,
                intent="scrape_completed",
                message_type=MessageType.SCRAPE_COMPLETED,
                payload={"results": results},
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Scraping failed for {last_name}: {str(e)}")
            return AgentMessage(
                agent_id=self.agent_id,
                intent="error_occurred",
                message_type=MessageType.ERROR_OCCURRED,
                payload={"error": str(e)},
                session_id=session_id
            )

    async def _perform_deep_scrape(self, session_id: str, results: List[Dict]) -> List[Dict]:
        """Perform deep scraping for each agent in the results to extract emails."""
        deep_results = []
        for agent in results:
            drill_id = agent.get("drill_id")
            if drill_id:
                try:
                    logger.info(f"Session {session_id}: Performing deep scrape for {agent.get('name')} (Drill ID: {drill_id})")
                    email = self.scraper.perform_drillthrough(drill_id)
                    if email:
                        agent["email"] = email
                except Exception as e:
                    logger.error(f"Deep scrape failed for {agent.get('name')}: {e}")
            
            deep_results.append(agent)
            # Add a small delay to avoid overwhelming the server
            await asyncio.sleep(1.0)
            
        return deep_results
