import pytest
import json
from unittest.mock import MagicMock, patch
from core.queue_manager import QueueManager

@pytest.fixture
def mock_redis():
    with patch('core.queue_manager.redis.from_url') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

def test_enqueue(mock_redis):
    qm = QueueManager()
    job = {"type": "test", "payload": {}}
    
    job_id = qm.enqueue(job)
    
    assert job_id is not None
    # Verify LPUSH was called with correct queue name and JSON string
    assert mock_redis.rpush.called
    args = mock_redis.rpush.call_args
    # args[0] is (name, value)
    assert args[0][0] == "reca_scraper_queue"  # Default name in class
    data = json.loads(args[0][1])
    assert data["type"] == "test"

def test_dequeue(mock_redis):
    qm = QueueManager()
    
    # Mock BRPOP response: (queue_name, data)
    job_data = {
        "job_id": "123",
        "type": "test",
        "status": "pending",
        "created_at": 1234567890
    }
    # Using blpop in implementation
    mock_redis.blpop.return_value = (b'reca_scraper_queue', json.dumps(job_data).encode('utf-8'))
    
    job = qm.dequeue()
    
    assert job is not None
    assert job["job_id"] == "123"
    assert mock_redis.blpop.called

def test_dequeue_empty(mock_redis):
    qm = QueueManager()
    mock_redis.blpop.return_value = None
    
    job = qm.dequeue()
    assert job is None

def test_get_queue_length(mock_redis):
    qm = QueueManager()
    mock_redis.llen.return_value = 5
    
    length = qm.get_queue_length()
    assert length == 5
