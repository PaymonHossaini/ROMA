import pytest
from unittest.mock import Mock

from sentientresearchagent.hierarchical_agent_framework.agent_configs.config_loader import AgentConfigLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.agent_factory import AgentFactory


def create_agent_by_name(factory: AgentFactory, config, agent_name: str):
    agents = config.get('agents', [])
    for ag in agents:
        name = ag.get('name') if hasattr(ag, 'get') else None
        if name == agent_name:
            return factory.create_agent(ag)
    return None


def test_search_executor_real_duckduckgo_tool():
    """Integration test: use the real DuckDuckGo tool created by the factory (performs a real web search).

    This verifies the agent factory wiring and the concrete DuckDuckGo tool implementation (network).
    """
    config_loader = AgentConfigLoader()
    config = config_loader.load_config()
    factory = AgentFactory(config_loader)

    # Create the SearchExecutor via factory config
    created = create_agent_by_name(factory, config, 'SearchExecutor')
    assert created is not None

    agno_agent = created.get('agno_agent')
    assert agno_agent is not None

    # Find the duckduckgo tool instance attached to the AgnoAgent
    tools = getattr(agno_agent, 'tools', [])
    dd_tool = None
    for t in tools:
        if hasattr(t, 'duckduckgo_search'):
            dd_tool = t
            break

    assert dd_tool is not None, "DuckDuckGo tool was not attached to the agent"

    # If the factory provided a Mock (some test environments patch agno.tools), try to
    # import and instantiate the real DuckDuckGoTools directly so we run an actual network search.
    if isinstance(dd_tool, Mock) or getattr(dd_tool, '__class__', None).__name__ == 'Mock':
        try:
            from agno.tools.duckduckgo import DuckDuckGoTools
            dd_tool = DuckDuckGoTools()
        except Exception as e:
            pytest.skip(f"Real DuckDuckGoTools not available: {e}")

    # Try calling the tool in-process first
    results = None
    try:
        results = dd_tool.duckduckgo_search("Who is the president of France?", max_results=3)
    except Exception:
        results = None

    # If the in-process call returned a Mock or something unusable (some test harnesses patch agno.tools),
    # run the real DuckDuckGoTools in an isolated Python subprocess to avoid in-process monkeypatching.
    def _is_usable(obj):
        from unittest.mock import Mock as _Mock
        return obj is not None and not isinstance(obj, _Mock)

    if not _is_usable(results) or not isinstance(results, (str, list, dict)):
        import subprocess, sys, json, textwrap

        script = textwrap.dedent("""
        import json, importlib
        mod = importlib.import_module('agno.tools.duckduckgo')
        inst = mod.DuckDuckGoTools()
        res = inst.duckduckgo_search('Who is the president of France?', max_results=3)
        if isinstance(res, str):
            try:
                parsed = json.loads(res)
            except Exception:
                parsed = res
        else:
            parsed = res
        print(json.dumps({'result': parsed}, ensure_ascii=False))
        """)

        proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.skip(f"Could not run isolated DuckDuckGoTools: {proc.stderr}")

        try:
            payload = json.loads(proc.stdout)
            results = payload.get('result')
        except Exception:
            pytest.fail("Isolated DuckDuckGoTools returned non-JSON output")

    # Some implementations return a JSON string; normalize to Python objects
    import json
    if isinstance(results, str):
        try:
            parsed = json.loads(results)
            results = parsed
        except Exception:
            pytest.fail("duckduckgo_search returned a string that is not valid JSON")

    # If the tool returns a dict wrapper like {"results": [...]}, extract it
    if isinstance(results, dict) and "results" in results:
        results = results["results"]

    # Normalize single-result dict to list
    if isinstance(results, dict):
        results = [results]

    assert isinstance(results, list), "Expected list of results from duckduckgo_search"
    assert len(results) > 0, "Expected at least one search result"

    first = results[0]
    # Support a few possible key names across implementations
    assert any(k in first for k in ("title", "href", "body", "link", "snippet")), f"Unexpected result keys: {list(first.keys())}"


def test_search_executor_real_wikipedia_tool():
    """Integration test: use the real WikipediaTools created by the factory (performs a real Wikipedia query).

    Falls back to isolated subprocess if the in-process tool or its methods are mocked by the test environment.
    """
    config_loader = AgentConfigLoader()
    config = config_loader.load_config()
    factory = AgentFactory(config_loader)

    # Create the SearchExecutor via factory config
    created = create_agent_by_name(factory, config, 'SearchExecutor')
    assert created is not None

    agno_agent = created.get('agno_agent')
    assert agno_agent is not None

    # Find the wikipedia tool instance attached to the AgnoAgent
    tools = getattr(agno_agent, 'tools', [])
    wp_tool = None
    for t in tools:
        if hasattr(t, 'search_wikipedia'):
            wp_tool = t
            break

    assert wp_tool is not None, "WikipediaTools was not attached to the agent"

    # If the factory provided a Mock, try to instantiate the real tool directly
    from unittest.mock import Mock as _Mock
    if isinstance(wp_tool, _Mock) or getattr(wp_tool, '__class__', None).__name__ == 'Mock':
        try:
            from agno.tools.wikipedia import WikipediaTools
            wp_tool = WikipediaTools()
        except Exception as e:
            pytest.skip(f"Real WikipediaTools not available: {e}")

    # Try calling in-process; inspect signature to call correctly
    import inspect
    results = None
    try:
        sig = None
        try:
            sig = inspect.signature(wp_tool.search_wikipedia)
        except Exception:
            sig = None

        if sig and 'max_results' in sig.parameters:
            results = wp_tool.search_wikipedia('Paris', max_results=3)
        elif sig and 'limit' in sig.parameters:
            results = wp_tool.search_wikipedia('Paris', limit=3)
        else:
            # Fallback to positional args or single-arg call
            try:
                results = wp_tool.search_wikipedia('Paris')
            except TypeError:
                results = None
    except Exception:
        results = None

    # Fallback to isolated subprocess if needed
    def _is_usable(obj):
        from unittest.mock import Mock as _Mock
        return obj is not None and not isinstance(obj, _Mock)

    if not _is_usable(results) or not isinstance(results, (str, list, dict)):
        import subprocess, sys, json, textwrap

        # Build a subprocess script that inspects the signature and calls correctly
        script = textwrap.dedent("""
        import json, importlib, inspect
        mod = importlib.import_module('agno.tools.wikipedia')
        inst = mod.WikipediaTools()
        func = inst.search_wikipedia
        sig = None
        try:
            sig = inspect.signature(func)
        except Exception:
            sig = None

        if sig and 'max_results' in sig.parameters:
            res = func('Paris', max_results=3)
        elif sig and 'limit' in sig.parameters:
            res = func('Paris', limit=3)
        else:
            try:
                res = func('Paris')
            except TypeError:
                res = None

        print(json.dumps({'result': res}, ensure_ascii=False))
        """)

        proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.skip(f"Could not run isolated WikipediaTools: {proc.stderr}")

        # Proc stdout may contain logging/info text before the JSON payload. Find the
        # last JSON-looking fragment and parse that. Be defensive and include
        # stdout/stderr in the failure message to aid debugging.
        try:
            out = proc.stdout or ""
            start = out.rfind('{"result')
            if start == -1:
                # try a generic JSON object/array at the end of the output
                # fall back to the last non-empty line
                lines = [l for l in out.splitlines() if l.strip()]
                candidate = lines[-1] if lines else out
            else:
                candidate = out[start:]

            # If candidate looks like JSON, try to load it. If not, raise to fail below.
            payload = None
            try:
                payload = json.loads(candidate)
            except Exception:
                # As a last resort, try to locate the first '{' from the end and parse
                alt_start = None
                for i in range(len(out) - 1, -1, -1):
                    if out[i] == '{' or out[i] == '[':
                        alt_start = i
                        break
                if alt_start is not None:
                    try:
                        payload = json.loads(out[alt_start:])
                    except Exception:
                        payload = None

            if not payload:
                raise ValueError('No JSON payload parsed')

            results = payload.get('result')
        except Exception as e:
            pytest.fail(f"Isolated WikipediaTools returned non-JSON output. stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}\nerror: {e}")

    # Normalize results
    import json
    if isinstance(results, str):
        try:
            parsed = json.loads(results)
            results = parsed
        except Exception:
            # keep as string if it's plain text
            results = [results]

    if isinstance(results, dict) and 'results' in results:
        results = results['results']

    if isinstance(results, dict):
        results = [results]

    assert isinstance(results, list), "Expected list from search_wikipedia"
    assert len(results) > 0, "Expected at least one Wikipedia result"

    first = results[0]
    # Wikipedia tool implementations vary. Accept several possible shapes.
    if isinstance(first, dict):
        allowed_keys = (
            'title', 'snippet', 'summary', 'link', 'content', 'name', 'meta_data', 'href', 'body'
        )
        assert any(k in first for k in allowed_keys), f"Unexpected keys: {list(first.keys())}"
