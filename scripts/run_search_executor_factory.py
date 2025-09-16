"""Run SearchExecutor agent creation via AgentFactory and show attached tools.

Usage:
    source .venv/bin/activate
    python scripts/run_search_executor_factory.py

This script loads the YAML agent configs using AgentConfigLoader, instantiates
AgentFactory, creates the agent named 'SearchExecutor' and prints useful info
about the created agent (tools, adapter type).
"""
import sys
import argparse
from pathlib import Path

# Ensure project src is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sentientresearchagent.hierarchical_agent_framework.agent_configs.config_loader import AgentConfigLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.agent_factory import AgentFactory


def create_agent_by_name(factory: AgentFactory, config, agent_name: str):
    agents = config.get('agents', [])
    for ag in agents:
        name = ag.get('name') if hasattr(ag, 'get') else None
        if name == agent_name:
            return factory.create_agent(ag)
    return None


def pretty_print_created(created: dict):
    adapter = created.get('adapter')
    agno_agent = created.get('agno_agent') or created.get('agent') or created.get('agent_instance')

    print(f"Created agent entry keys: {list(created.keys())}")

    if agno_agent:
        tools = getattr(agno_agent, 'tools', None)
        if tools is None:
            print("No tools attached to AgnoAgent (tools is None)")
        else:
            print(f"AgnoAgent has {len(tools)} tools:")
            for i, t in enumerate(tools):
                try:
                    tname = type(t).__name__
                except Exception:
                    tname = str(t)
                print(f"  {i+1}. {tname}")
    else:
        print("No AgnoAgent instance was created for this agent (it might be a custom adapter)")

    if adapter:
        print("Adapter type:", type(adapter).__name__)
    else:
        print("No adapter returned in created agent dict")


def main():
    parser = argparse.ArgumentParser(description="Create agent via AgentFactory and optionally run it")
    parser.add_argument('--agent-name', default='SearchExecutor', help='Agent name to create from YAML')
    parser.add_argument('--run', action='store_true', help='If set, run the created AgnoAgent with --query')
    parser.add_argument('--query', type=str, default='What is the capital of France?', help='Query to run when --run is specified')

    args = parser.parse_args()

    loader = AgentConfigLoader()
    config = loader.load_config()

    factory = AgentFactory(loader)

    created = create_agent_by_name(factory, config, args.agent_name)
    if not created:
        print(f"Agent '{args.agent_name}' not found in configuration")
        return 2

    pretty_print_created(created)

    if args.run:
        agno_agent = created.get('agno_agent') or created.get('agent') or created.get('agent_instance')
        if not agno_agent:
            print("No AgnoAgent to run for this agent")
            return 3

        print(f"\nRunning agent '{args.agent_name}' with query: {args.query}\n")
        try:
            # Use print_response to show the agent's textual output; this may call external tools
            response = agno_agent.print_response(args.query, markdown=False)
            print("Agent response:\n", response)
        except Exception as e:
            print("Agent run failed:", e)
            return 4

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
