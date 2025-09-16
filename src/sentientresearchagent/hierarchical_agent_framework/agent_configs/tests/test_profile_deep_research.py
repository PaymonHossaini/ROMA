import pytest

from sentientresearchagent.hierarchical_agent_framework.agent_configs.profile_loader import ProfileLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.config_loader import AgentConfigLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.agent_factory import AgentFactory
from sentientresearchagent.hierarchical_agent_framework.types import TaskType


def create_agent_by_name(factory: AgentFactory, config, agent_name: str):
    agents = config.get('agents', [])
    for ag in agents:
        name = ag.get('name') if hasattr(ag, 'get') else None
        if name == agent_name:
            return factory.create_agent(ag)
    return None


def test_deep_research_profile_search_executor_has_tools():
    """Load deep_research_agent profile and ensure its SEARCH executor has expected tools."""
    # Load the profile file (by filename stem)
    loader = ProfileLoader()
    blueprint = loader.load_profile('deep_research_agent')

    # Determine the configured executor adapter name for SEARCH
    search_executor_name = blueprint.executor_adapter_names.get(TaskType.SEARCH)
    assert search_executor_name is not None, "Profile must specify a SEARCH executor"

    # Load agents.yaml and create the agent via AgentFactory
    config_loader = AgentConfigLoader()
    config = config_loader.load_config()
    factory = AgentFactory(config_loader)

    created = create_agent_by_name(factory, config, search_executor_name)
    assert created is not None, f"Agent '{search_executor_name}' should be present in agents.yaml"

    agno_agent = created.get('agno_agent') or created.get('agent') or created.get('agent_instance')
    assert agno_agent is not None, "Factory should create an AgnoAgent for the SearchExecutor"

    tools = getattr(agno_agent, 'tools', None)
    assert isinstance(tools, list), "AgnoAgent.tools should be a list"

    # Ensure there is at least one search tool and that it exposes the expected API.
    # Tests may mock classes at runtime, so check for capabilities (duckduckgo_search) instead
    assert len(tools) > 0, "Expected at least one tool attached to the SearchExecutor"

    # DuckDuckGo tool should provide a 'duckduckgo_search' callable (or be a Mock exposing that attr)
    dd_tool_ok = any(hasattr(t, 'duckduckgo_search') for t in tools)
    assert dd_tool_ok, "A DuckDuckGo-like tool (with duckduckgo_search) should be attached to the SearchExecutor"

    # WikipediaTools may be optional if dependency missing; only assert if importable
    try:
        import importlib
        importlib.import_module('agno.tools.wikipedia')
        wiki_expected = True
    except Exception:
        wiki_expected = False

    if wiki_expected:
        wiki_tool_ok = any(hasattr(t, 'search_wikipedia') for t in tools)
        assert wiki_tool_ok, "WikipediaTools should be attached to the SearchExecutor when available"
