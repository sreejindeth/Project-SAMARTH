"""
Plugin Module - Auto-imports all plugins for registration
"""

# Import plugins to trigger their auto-registration
from .compare_rainfall_crops_plugin import CompareRainfallCropsPlugin
from .district_extremes_plugin import DistrictExtremesPlugin
from .production_trend_plugin import ProductionTrendPlugin
from .policy_arguments_plugin import PolicyArgumentsPlugin

__all__ = [
    "CompareRainfallCropsPlugin",
    "DistrictExtremesPlugin",
    "ProductionTrendPlugin",
    "PolicyArgumentsPlugin",
]
