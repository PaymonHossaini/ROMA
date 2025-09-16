#!/usr/bin/env python3
"""Quick repro: instantiate SearchExecutor via AgentFactory and run a single execution task.
"""
import asyncio
import os
import logging
from loguru import logger

from sentientresearchagent.hierarchical_agent_framework.agent_configs.config_loader import AgentConfigLoader
from sentientresearchagent.hierarchical_agent_framework.agent_configs.agent_factory import AgentFactory
from sentientresearchagent.hierarchical_agent_framework.node.task_node import TaskNode
from sentientresearchagent.hierarchical_agent_framework.context.agent_io_models import AgentTaskInput

async def main():
    logger.info("Starting repro script: create SearchExecutor and run a search task")
    loader = AgentConfigLoader()
    factory = AgentFactory(loader)
    # Load the validated agents config and get the SearchExecutor definition
    config = loader.load_config()
    search_agent_cfg = None
    for a in config.agents:
        if a.name == 'SearchExecutor':
            search_agent_cfg = a
            break
    if not search_agent_cfg:
        logger.error('SearchExecutor not found in agents.yaml')
        return

    agent_info = factory.create_agent(search_agent_cfg)
    adapter = agent_info.get('adapter')
    agno_agent = agent_info.get('agno_agent')
    logger.info(f"Created adapter: {type(adapter).__name__}; agno_agent: {type(agno_agent).__name__}")

    # Build a simple TaskNode and AgentTaskInput
    node = TaskNode(task_id='test-search-1', goal='Search Wikipedia for "Artificial intelligence"')
    task_input = AgentTaskInput.current_goal = None

    # Construct proper AgentTaskInput via model import
    from sentientresearchagent.hierarchical_agent_framework.context.agent_io_models import AgentTaskInput
    ati = AgentTaskInput(
        overall_project_goal='Test project',
        current_goal='Artificial intelligence',
        relevant_context_items=[],
        overall_objective='Test search for AI',
        formatted_full_context=None
    )

    # Use a lightweight TraceManager stub
    class _StubTraceManager:
        def get_trace_for_node(self, node_id):
            return None
        def create_trace(self, node_id, goal):
            return None
        def get_stage(self, *args, **kwargs):
            return None
        def start_stage(self, *args, **kwargs):
            return None
        def update_stage(self, *args, **kwargs):
            return None
        def complete_stage(self, *args, **kwargs):
            return None

    trace = _StubTraceManager()

    try:
        result = await adapter.process(node, ati, trace)
        logger.info('Adapter result:')
        logger.info(result)
    except Exception as e:
        logger.exception('Adapter run failed')

if __name__ == '__main__':
    asyncio.run(main())
