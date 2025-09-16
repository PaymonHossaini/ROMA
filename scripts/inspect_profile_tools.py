#!/usr/bin/env python3
"""Inspect profile agents and print attached AgnoAgent tools.

Usage: ./scripts/inspect_profile_tools.py

This script loads a profile YAML (default: src/.../profiles/general_agent.yaml),
creates agents via AgentFactory, and prints diagnostics about attached tools.
"""
import sys
import os
import yaml
import traceback

from sentientresearchagent.hierarchical_agent_framework.agent_configs.config_loader import AgentConfigLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.agent_factory import AgentFactory
from sentientresearchagent.hierarchical_agent_framework.agent_configs.profile_loader import ProfileLoader

PROFILE_PATH = os.path.join(
    "src",
    "sentientresearchagent",
    "hierarchical_agent_framework",
    "agent_configs",
    "profiles",
    "general_agent.yaml",
)


def pretty_print_tools(agno_agent):
    tools = getattr(agno_agent, 'tools', None)
    if not tools:
        print('    [no tools attached]')
        return
    for idx, t in enumerate(tools, 1):
        try:
            cls_name = t.__class__.__name__
        except Exception:
            cls_name = str(type(t))
        # try common attributes
        name = getattr(t, 'name', None) or getattr(t, '__name__', None) or ''
        print(f"    {idx}. {cls_name} {f'({name})' if name else ''}")


def main(profile_path=PROFILE_PATH):
    print(f"Loading profile: {profile_path}")
    if not os.path.exists(profile_path):
        print("Profile not found:", profile_path)
        sys.exit(2)

    with open(profile_path, 'r') as f:
        profile = yaml.safe_load(f)

    if not profile or 'profile' not in profile:
        print('Profile file missing top-level "profile" key')
        sys.exit(2)

    profile_cfg = profile['profile']

    try:
        loader = AgentConfigLoader()
        factory = AgentFactory(loader)
    except Exception as e:
        print('Failed to create AgentFactory:')
        traceback.print_exc()
        sys.exit(1)

    try:
        created = factory.create_agents_for_profile(profile_cfg)
    except Exception as e:
        print('Error creating agents from profile:')
        traceback.print_exc()
        sys.exit(1)

    # If the profile didn't explicitly define agents, attempt to interpret it as a blueprint
    if not created:
        print('No explicit agents created from profile; attempting blueprint-based creation...')
        try:
            loader = ProfileLoader()
            blueprint = loader.load_profile(os.path.splitext(os.path.basename(profile_path))[0])
            created = factory.create_agents_from_blueprint(blueprint)
        except Exception:
            print('Blueprint-based creation failed:')
            traceback.print_exc()
            return

    if not created:
        print('No agents were created from the profile')
        return

    print('\nCreated agents:')
    for name, info in created.items():
        print('\n- Agent:', name)
        ag = info.get('agno_agent')
        adapter = info.get('adapter')
        print('  Adapter:', type(adapter).__name__ if adapter else None)
        if not ag:
            print('  AgnoAgent: None')
            continue
        print('  AgnoAgent present')
        pretty_print_tools(ag)


if __name__ == '__main__':
    main()
