"""
Core Query Engine - Uses Plugin Registry to Route Requests

This is the STRATEGY PATTERN in action:
- Engine doesn't know about specific query types
- It delegates to registered plugins
- Easy to add new query types without modifying engine
"""
from typing import Dict, Any
import pandas as pd
from .plugin_base import plugin_registry


class QueryEngine:
    """
    Core engine that routes queries to appropriate plugins.
    """

    def __init__(self, data_manager):
        """
        Initialize engine with data manager.

        Args:
            data_manager: DataManager instance for accessing datasets
        """
        self.data_manager = data_manager
        self.registry = plugin_registry

    def execute_query(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a query using the appropriate plugin.

        Args:
            intent: Question intent (e.g., 'compare_rainfall_and_crops')
            params: Extracted parameters

        Returns:
            Query result with answer, tables, citations

        Raises:
            ValueError: If no plugin can handle the intent/params
        """
        # Find plugin
        plugin = self.registry.find_plugin_for_params(intent, params)

        if not plugin:
            available = list(self.registry.list_plugins().keys())
            raise ValueError(
                f"No plugin found for intent '{intent}'. "
                f"Available: {', '.join(available)}"
            )

        # Validate parameters
        is_valid, error_msg = plugin.validate_params(params)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {error_msg}")

        # Load required data
        data = {
            "agriculture": self.data_manager.load_dataset("agriculture"),
            "rainfall": self.data_manager.load_dataset("rainfall"),
        }

        # Execute plugin
        result = plugin.execute(params, data)

        # Add debug info
        result["debug"] = {
            "intent": intent,
            "plugin": plugin.intent_name,
            "params": params
        }

        return result

    def list_available_queries(self) -> Dict[str, str]:
        """List all supported query types."""
        return self.registry.list_plugins()
