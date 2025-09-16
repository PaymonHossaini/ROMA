"""
Blueprint utilities extracted to a neutral module to avoid import cycles.
This module provides helper functions used by node code and registry code
without importing heavy modules that would trigger circular imports.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from sentientresearchagent.hierarchical_agent_framework.node.task_node import TaskNode
    from sentientresearchagent.hierarchical_agent_framework.agent_blueprints import AgentBlueprint


def apply_blueprint_to_node(node: "TaskNode", blueprint: "AgentBlueprint", action_verb: str) -> bool:
    """
    Apply blueprint configuration to a TaskNode based on action and node level.

    Args:
        node: TaskNode to configure
        blueprint: AgentBlueprint to apply
        action_verb: The action being performed

    Returns:
        bool: True if successfully applied, False otherwise
    """
    try:
        # Determine if this is the root node
        is_root_node = (node.task_id == "root" or 
                       getattr(node, 'level', 0) == 0 or
                       getattr(node, 'parent_id', None) is None)

        if action_verb.lower() == "plan":
            # For planning, check if we should use root-specific planner
            if is_root_node and blueprint.root_planner_adapter_name:
                agent_name = blueprint.root_planner_adapter_name
                logger.info(f"🎯 Using ROOT planner '{agent_name}' for root node {node.task_id}")
            elif node.task_type and node.task_type in blueprint.planner_adapter_names:
                agent_name = blueprint.planner_adapter_names[node.task_type]
                logger.info(f"📋 Using task-specific planner '{agent_name}' for {node.task_type} node {node.task_id}")
            else:
                agent_name = blueprint.default_planner_adapter_name
                logger.info(f"📋 Using default planner '{agent_name}' for node {node.task_id}")
                
        elif action_verb.lower() == "execute":
            # For execution, use task-specific executors
            if node.task_type and node.task_type in blueprint.executor_adapter_names:
                agent_name = blueprint.executor_adapter_names[node.task_type]
            else:
                agent_name = blueprint.default_executor_adapter_name
                
        elif action_verb.lower() == "atomize":
            agent_name = blueprint.atomizer_adapter_name
        elif action_verb.lower() == "aggregate":
            agent_name = blueprint.aggregator_adapter_name
        elif action_verb.lower() == "modify_plan":
            agent_name = blueprint.plan_modifier_adapter_name
        else:
            logger.warning(f"Unknown action_verb '{action_verb}' for blueprint application")
            return False

        if agent_name:
            node.agent_name = agent_name
            logger.info(f"✅ Applied blueprint: Node {node.task_id} -> Agent '{agent_name}' for action '{action_verb}'")
            return True
        else:
            logger.warning(f"No agent name found for action '{action_verb}' in blueprint '{blueprint.name}'")
            return False
            
    except Exception as e:
        logger.error(f"Error applying blueprint to node {node.task_id}: {e}")
        return False
