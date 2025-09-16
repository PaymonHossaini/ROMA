import pytest


def test_duckduckgo_tool_instantiates():
    """Ensure the DuckDuckGo tool class can be imported and instantiated."""
    from agno.tools.duckduckgo import DuckDuckGoTools

    tool = DuckDuckGoTools()
    assert tool is not None


def test_wikipedia_tool_instantiates():
    """Ensure the Wikipedia tool class can be imported and instantiated."""
    from agno.tools.wikipedia import WikipediaTools

    tool = WikipediaTools()
    assert tool is not None