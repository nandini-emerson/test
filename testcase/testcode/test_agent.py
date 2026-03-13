
import pytest
import os
from unittest.mock import patch, MagicMock

# Assume the agent class is named Agent and is imported from agent_module
# from agent_module import Agent

@pytest.fixture
def valid_openai_env(monkeypatch):
    """
    Fixture to set up valid OpenAI API key and LLM provider in environment variables.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-validkey1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "openai")


@pytest.fixture
def mock_llm_client():
    """
    Fixture to mock the LLM client used by the Agent.
    """
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def agent_class():
    """
    Fixture to provide the Agent class. Replace with actual import if available.
    """
    class DummyAgent:
        def __init__(self):
            api_key = os.environ.get("OPENAI_API_KEY")
            provider = os.environ.get("LLM_PROVIDER", "openai")
            if not api_key:
                raise ValueError("OPENAI_API_KEY missing")
            if not api_key.startswith("sk-"):
                raise ValueError("Invalid API key format")
            self.llm_client = MagicMock()
    return DummyAgent


def test_agent_initialization_with_valid_openai_api_key(valid_openai_env, agent_class):
    """
    Functional test:
    Validates that the agent initializes correctly when a valid OpenAI API key is present in the environment.
    Ensures Agent instance is created, llm_client is initialized, and no exceptions are raised.
    """
    agent = None
    try:
        agent = agent_class()
    except Exception as e:
        pytest.fail(f"Agent initialization raised an exception: {e}")

    assert agent is not None, "Agent instance should not be None"
    assert getattr(agent, "llm_client", None) is not None, "Agent.llm_client should be initialized"


@pytest.mark.parametrize("env_vars,expected_exception", [
    ({"LLM_PROVIDER": "openai"}, ValueError),  # Missing OPENAI_API_KEY
    ({"OPENAI_API_KEY": "invalidkey", "LLM_PROVIDER": "openai"}, ValueError),  # Invalid API key format
])
def test_agent_initialization_error_scenarios(monkeypatch, agent_class, env_vars, expected_exception):
    """
    Functional edge-case test:
    Validates agent initialization error scenarios:
    - Missing OPENAI_API_KEY
    - Invalid API key format
    Ensures appropriate exceptions are raised.
    """
    # Clear environment variables first
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

    with pytest.raises(expected_exception):
        agent_class()

