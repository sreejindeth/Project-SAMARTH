"""
Base Plugin System for Project Samarth

This demonstrates the PLUGIN ARCHITECTURE pattern where:
- Each question type is a separate plugin
- Plugins register themselves with the PluginRegistry
- Core engine routes requests to appropriate plugins
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class QueryPlugin(ABC):
    """Base class for all query plugins."""

    @property
    @abstractmethod
    def intent_name(self) -> str:
        """Unique identifier for this plugin's intent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this plugin does."""
        pass

    @abstractmethod
    def can_handle(self, params: Dict[str, Any]) -> bool:
        """
        Check if this plugin can handle the given parameters.

        Args:
            params: Parsed question parameters

        Returns:
            True if plugin can handle this request
        """
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Execute the query using provided parameters and data.

        Args:
            params: Parsed question parameters
            data: Dictionary of DataFrames (agriculture, rainfall, etc.)

        Returns:
            Dictionary with 'answer', 'tables', 'citations'
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters before execution.

        Returns:
            (is_valid, error_message)
        """
        return True, None


class PluginRegistry:
    """
    Registry for managing query plugins.

    Demonstrates the REGISTRY PATTERN for dynamic plugin discovery.
    """

    def __init__(self):
        self._plugins: Dict[str, QueryPlugin] = {}

    def register(self, plugin: QueryPlugin):
        """Register a new plugin."""
        intent = plugin.intent_name
        if intent in self._plugins:
            raise ValueError(f"Plugin for intent '{intent}' already registered")
        self._plugins[intent] = plugin
        print(f"✓ Registered plugin: {intent} - {plugin.description}")

    def get_plugin(self, intent: str) -> Optional[QueryPlugin]:
        """Get plugin by intent name."""
        return self._plugins.get(intent)

    def list_plugins(self) -> Dict[str, str]:
        """List all registered plugins."""
        return {
            intent: plugin.description
            for intent, plugin in self._plugins.items()
        }

    def find_plugin_for_params(self, intent: str, params: Dict[str, Any]) -> Optional[QueryPlugin]:
        """Find the best plugin to handle given parameters."""
        plugin = self.get_plugin(intent)
        if plugin and plugin.can_handle(params):
            return plugin
        return None


# Global registry instance
plugin_registry = PluginRegistry()
