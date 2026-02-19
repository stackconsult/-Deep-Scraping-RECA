import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from agents.reca_scraper_agent import RECAScraperAgent
from schemas.messages import AgentMessage, MessageType
from uuid import uuid4

@pytest.fixture
def mock_model_router():
    return MagicMock()

@pytest.fixture
def mock_queue_manager():
    with patch('agents.reca_scraper_agent.QueueManager') as mock:
        qm_instance = MagicMock()
        mock.return_value = qm_instance
        yield qm_instance

@pytest.fixture
def mock_http_scraper():
    with patch('agents.reca_scraper_agent.RECAHttpScraper') as mock:
        scraper_instance = MagicMock()
        mock.return_value = scraper_instance
        yield scraper_instance

@pytest.mark.asyncio
async def test_async_scrape_request_success(mock_model_router, mock_queue_manager, mock_http_scraper):
    agent = RECAScraperAgent(mock_model_router)
    # Ensure queue manager is mocked
    agent.queue_manager = mock_queue_manager
    
    mock_queue_manager.enqueue.return_value = "job-123"
    
    message = AgentMessage(
        agent_id="test_client",
        intent="scrape_request",
        message_type=MessageType.SCRAPE_REQUEST,
        payload={
            "search_params": {"last_name": "Smith"},
            "async": True
        },
        session_id=str(uuid4())
    )
    
    response = await agent.process_message(message)
    
    assert response is not None
    assert response.message_type == MessageType.JOB_QUEUED
    assert response.payload["job_id"] == "job-123"
    assert response.payload["status"] == "queued"
    
    mock_queue_manager.enqueue.assert_called_once()
    # Sync scraper should NOT be called
    mock_http_scraper.search_by_lastname.assert_not_called()

@pytest.mark.asyncio
async def test_async_scrape_request_failure(mock_model_router, mock_queue_manager, mock_http_scraper):
    agent = RECAScraperAgent(mock_model_router)
    agent.queue_manager = mock_queue_manager
    
    mock_queue_manager.enqueue.side_effect = Exception("Queue error")
    
    message = AgentMessage(
        agent_id="test_client",
        intent="scrape_request",
        message_type=MessageType.SCRAPE_REQUEST,
        payload={
            "search_params": {"last_name": "Smith"},
            "async": True
        },
        session_id=str(uuid4())
    )
    
    response = await agent.process_message(message)
    
    assert response is not None
    assert response.message_type == MessageType.ERROR_OCCURRED
    assert "Failed to queue job" in response.payload["error"]
    
    mock_queue_manager.enqueue.assert_called_once()

@pytest.mark.asyncio
async def test_sync_scrape_request(mock_model_router, mock_queue_manager, mock_http_scraper):
    agent = RECAScraperAgent(mock_model_router)
    agent.queue_manager = mock_queue_manager
    
    mock_http_scraper.search_by_lastname.return_value = [{"name": "John Smith"}]
    
    message = AgentMessage(
        agent_id="test_client",
        intent="scrape_request",
        message_type=MessageType.SCRAPE_REQUEST,
        payload={
            "search_params": {"last_name": "Smith"},
            # async defaults to False
        },
        session_id=str(uuid4())
    )
    
    response = await agent.process_message(message)
    
    assert response is not None
    assert response.message_type == MessageType.SCRAPE_COMPLETED
    assert len(response.payload["results"]) == 1
    
    mock_queue_manager.enqueue.assert_not_called()
    mock_http_scraper.search_by_lastname.assert_called_once_with("Smith")
