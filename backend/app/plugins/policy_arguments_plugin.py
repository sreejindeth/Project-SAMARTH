"""
Policy Arguments Plugin

Generates data-driven policy arguments for crop shift decisions.
"""
from typing import Dict, Any, Optional, List
import pandas as pd
from ..core.plugin_base import QueryPlugin, plugin_registry


class PolicyArgumentsPlugin(QueryPlugin):
    """
    Plugin for handling: "Policy arguments for crop shift"

    Sample Prompt for THIS plugin (Project 2):
    "Should we shift from Cotton to Maize in Karnataka?
     Provide data-driven policy arguments using rainfall and production data."
    """

    @property
    def intent_name(self) -> str:
        return "policy_arguments"

    @property
    def description(self) -> str:
        return "Generate policy arguments for crop shift"

    def can_handle(self, params: Dict[str, Any]) -> bool:
        """Check if we have required parameters."""
        required = ["region", "crop_a", "crop_b"]
        return all(params.get(key) for key in required)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters."""
        if not params.get("region"):
            return False, "Missing region parameter"
        if not params.get("crop_a"):
            return False, "Missing crop_a parameter"
        if not params.get("crop_b"):
            return False, "Missing crop_b parameter"
        return True, None

    def execute(self, params: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Execute policy arguments query."""
        state = params["region"]
        current_crop = params["crop_a"]
        proposed_crop = params["crop_b"]
        n_years = params.get("years", 5)

        agri_df = data["agriculture"]
        rainfall_df = data["rainfall"]

        # Filter agriculture data for the state
        relevant = agri_df[agri_df["state"] == state]

        # Select years
        years_available = sorted(relevant["year"].unique(), reverse=True)
        years_to_use = n_years if n_years else min(len(years_available), 5)
        years_sel = sorted(years_available[:years_to_use])

        subset = relevant[relevant["year"].isin(years_sel)]

        # Aggregate data for both crops
        agg = (
            subset[subset["crop"].isin([current_crop, proposed_crop])]
            .groupby(["crop", "year"])["production_tonnes"]
            .sum()
            .reset_index()
        )

        # Get rainfall data
        rainfall = (
            rainfall_df[(rainfall_df["state"] == state) & (rainfall_df["year"].isin(years_sel))]
            .sort_values("year")
        )

        insights = []
        tables = []

        # Analyze each crop
        for crop in [current_crop, proposed_crop]:
            crop_series = agg[agg["crop"] == crop].sort_values("year")
            if crop_series.empty:
                insights.append(f"No production records for {crop} in {state}.")
                continue

            growth = self._calc_growth(crop_series)
            avg_prod = crop_series["production_tonnes"].mean()
            insights.append(
                f"{crop}: avg {avg_prod:.1f} tonnes over {len(years_sel)} year(s) with {growth:.1f}% total change."
            )

            tables.append({
                "title": f"{crop} production",
                "headers": ["Year", "Production (tonnes)"],
                "rows": [
                    [int(row["year"]), float(round(float(row["production_tonnes"]), 2))]
                    for _, row in crop_series.iterrows()
                ]
            })

        # Add rainfall context
        if not rainfall.empty:
            avg_rain = rainfall["annual_rainfall_mm"].mean()
            trend = self._calc_growth(rainfall)
            insights.append(
                f"Rainfall averaged {avg_rain:.1f} mm with {trend:.1f}% change, "
                f"affecting water availability for {proposed_crop}."
            )
            tables.append({
                "title": "Rainfall context",
                "headers": ["Year", "Rainfall (mm)"],
                "rows": [
                    [int(row["year"]), float(round(float(row["annual_rainfall_mm"]), 1))]
                    for _, row in rainfall.iterrows()
                ]
            })

        # Generate answer
        answer = (
            f"Supporting a shift towards {proposed_crop}: "
            + "; ".join(insights[:3])
        )

        # Citations
        citations = [
            {
                "dataset": "agriculture",
                "source": "https://data.gov.in/resources/district-wise-crop-production-statistics",
                "resource_id": "9ef84268-d588-465a-a308-a864a43d0070"
            },
            {
                "dataset": "rainfall",
                "source": "https://data.gov.in/resources/rainfall-sub-division-wise-distribution",
                "resource_id": "cca5f77c-68b3-43df-bd01-beb3b69204ed"
            }
        ]

        return {
            "answer": answer,
            "tables": tables,
            "citations": citations
        }

    @staticmethod
    def _calc_growth(series: pd.DataFrame) -> float:
        """Calculate percentage growth from first to last value."""
        series = series.sort_values(series.columns[0])
        values = series.iloc[:, -1].astype(float)
        if len(values) < 2 or values.iloc[0] == 0:
            return 0.0
        return ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100.0


# Auto-register this plugin
plugin_registry.register(PolicyArgumentsPlugin())
