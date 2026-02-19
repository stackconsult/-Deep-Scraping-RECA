import pytest
import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4
from core.model_router import ModelRouter

from agents.reca_scraper_agent import RECAScraperAgent
from schemas.messages import AgentMessage, MessageType

@pytest.fixture
def mock_model_router():
    return MagicMock(spec=ModelRouter)

@pytest.fixture
def agent(mock_model_router):
    return RECAScraperAgent(mock_model_router)

@pytest.mark.asyncio
async def test_handle_scrape_request_success(agent):
    # Mock the underlying scraper's search_by_lastname method
    mock_results = [{"name": "John Smith", "email": "john@example.com"}]
    with patch.object(agent.scraper, 'search_by_lastname', return_value=mock_results):
        
        message = AgentMessage(
            agent_id="test_sender",
            intent="start_scrape",
            message_type=MessageType.SCRAPE_REQUEST,
            payload={"search_params": {"last_name": "Smith"}},
            session_id=uuid4()
        )
        
        response = await agent.process_message(message)
        
        assert response is not None
        assert response.message_type == MessageType.SCRAPE_COMPLETED
        assert response.payload["results"] == mock_results

@pytest.mark.asyncio
async def test_handle_scrape_request_missing_params(agent):
    message = AgentMessage(
        agent_id="test_sender",
        intent="start_scrape",
        message_type=MessageType.SCRAPE_REQUEST,
        payload={"search_params": {}},  # Missing last_name
        session_id=uuid4()
    )
    
    response = await agent.process_message(message)
    
    assert response is not None
    assert response.message_type == MessageType.ERROR_OCCURRED
    assert "Missing 'last_name'" in response.payload["error"]

@pytest.mark.asyncio
async def test_handle_scrape_request_error(agent):
    with patch.object(agent.scraper, 'search_by_lastname', side_effect=Exception("Connection error")):
        
        message = AgentMessage(
            agent_id="test_sender",
            intent="start_scrape",
            message_type=MessageType.SCRAPE_REQUEST,
            payload={"search_params": {"last_name": "Smith"}},
            session_id=uuid4()
        )
        
        response = await agent.process_message(message)
        
        assert response is not None
        assert response.message_type == MessageType.ERROR_OCCURRED
        assert "Connection error" in response.payload["error"]
@pytest.mark.asyncio
async def test_handle_scrape_request_deep_scrape(agent):
    # Mock search_by_lastname to return a result with drill_id
    mock_results = [{"name": "John Smith", "drill_id": "12345"}]
    # Mock perform_drillthrough to return an email
    with patch.object(agent.scraper, 'search_by_lastname', return_value=mock_results):
        with patch.object(agent.scraper, 'perform_drillthrough', return_value="john@example.com"):
            
            message = AgentMessage(
                agent_id="test_sender",
                intent="start_scrape",
                message_type=MessageType.SCRAPE_REQUEST,
                payload={"search_params": {"last_name": "Smith"}, "deep_scrape": True},
                session_id=uuid4()
            )
            
            response = await agent.process_message(message)
            
            assert response is not None
            assert response.message_type == MessageType.SCRAPE_COMPLETED
            # Verify email was added
            assert response.payload["results"][0]["email"] == "john@example.com"
