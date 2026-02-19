import pytest
import json
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.context_aware_orchestrator import ContextAwareOrchestrator
from core.model_router import ModelRouter
from agents.repository_analyzer import RepositoryAnalyzerAgent

@pytest.fixture
def mock_router():
    return MagicMock(spec=ModelRouter)

@pytest.fixture
def mock_redis():
    mock = MagicMock()
    # Mock redis client methods
    mock.get.return_value = None
    mock.set.return_value = True
    return mock

@pytest.fixture
def orchestrator(mock_router, mock_redis):
    # We need to mock MessageBus because it tries to connect to real Redis
    with patch('orchestrator.context_aware_orchestrator.MessageBus') as MockMessageBus:
        mock_bus_instance = MockMessageBus.return_value
        mock_bus_instance.redis_client = mock_redis
        
        orch = ContextAwareOrchestrator(mock_router)
        return orch

@pytest.mark.asyncio
async def test_initialization_defaults(mock_router):
    """Test initialization with default agents."""
    with patch('orchestrator.context_aware_orchestrator.MessageBus'):
        orch = ContextAwareOrchestrator(mock_router)
        assert orch.repository_analyzer is not None
        assert orch.requirements_extractor is not None
        # Verify AsyncFileReader was injected
        assert hasattr(orch, 'file_reader')

@pytest.mark.asyncio
async def test_dependency_injection(mock_router):
    """Test initialization with injected agents."""
    mock_analyzer = MagicMock(spec=RepositoryAnalyzerAgent)
    
    with patch('orchestrator.context_aware_orchestrator.MessageBus'):
        orch = ContextAwareOrchestrator(
            mock_router, 
            repository_analyzer=mock_analyzer
        )
        assert orch.repository_analyzer == mock_analyzer

@pytest.mark.asyncio
async def test_session_persistence(orchestrator, mock_redis, caplog):
    """Test session saving and loading."""
    import logging
    
    session_id = "123e4567-e89b-12d3-a456-426614174000"
    data = {"test": "data"}
    
    # Force set redis client to ensure connection
    orchestrator.message_bus.redis_client = mock_redis
    
    # Test saving
    with caplog.at_level(logging.WARNING):
        await orchestrator._save_session(session_id, data)
    
    # Fail if any warnings/errors were logged (meaning exception was swallowed)
    errors = [r.message for r in caplog.records if r.levelname in ("WARNING", "ERROR")]
    if errors:
        with open("test_failure.log", "w") as f:
            f.write("\n".join(errors))
        pytest.fail(f"Operation failed with logs: {errors}")
    
    print(f"DEBUG: redis set calls: {mock_redis.set.mock_calls}")
    
    mock_redis.set.assert_called_once()
    args, _ = mock_redis.set.call_args
    assert f"session:{session_id}" == args[0]
    assert json.dumps(data) in args[1] or json.dumps(data) == args[1]
    
    # Test loading
    mock_redis.get.return_value = json.dumps(data)
    
    # Clear local memory to force load
    orchestrator.active_sessions.clear()
    
    await orchestrator._load_session(session_id)
    
    # Check if loaded (converting session_id to UUID if needed by implementation)
    uid = UUID(session_id)
    assert uid in orchestrator.active_sessions
    assert orchestrator.active_sessions[uid] == data

@pytest.mark.asyncio
async def test_file_reader_integration(orchestrator):
    """Test that AsyncFileReader is integrated."""
    from core.file_reader import AsyncFileReader
    assert isinstance(orchestrator.file_reader, AsyncFileReader)
