"""
Example Plugin: Compare Rainfall and Crops

This demonstrates how to implement a QueryPlugin.
Teammates should follow this pattern for the other 3 plugins.
"""
from typing import Dict, Any, Optional
import pandas as pd
from ..core.plugin_base import QueryPlugin, plugin_registry


class CompareRainfallCropsPlugin(QueryPlugin):
    """
    Plugin for handling: "Compare rainfall in State A and State B + top crops"

    Sample Prompt for THIS plugin (Project 2):
    "Compare average rainfall in Punjab and Tamil Nadu over last 5 years.
     Show top 3 Rice producing districts in each state."
    """

    @property
    def intent_name(self) -> str:
        return "compare_rainfall_and_crops"

    @property
    def description(self) -> str:
        return "Compare rainfall between states and rank top crops"

    def can_handle(self, params: Dict[str, Any]) -> bool:
        """Check if we have required parameters."""
        required = ["state_a", "state_b"]
        return all(params.get(key) for key in required)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate state names and crop filters."""
        if not params.get("state_a"):
            return False, "Missing state_a parameter"
        if not params.get("state_b"):
            return False, "Missing state_b parameter"
        return True, None

    def execute(self, params: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Execute the comparison query."""
        state_a = params["state_a"]
        state_b = params["state_b"]
        last_n_years = params.get("years", 5)
        crop_filter = params.get("crop_filter")
        top_m = params.get("top_m", 3)

        # Get dataframes
        rainfall_df = data["rainfall"]
        agri_df = data["agriculture"]

        # Filter rainfall data for both states
        rainfall = rainfall_df[rainfall_df["state"].isin([state_a, state_b])]
        available_years = sorted(rainfall["year"].unique(), reverse=True)

        if not available_years:
            raise ValueError("No rainfall data found for the requested states.")

        n_years = last_n_years if last_n_years else min(len(available_years), 5)
        years_sel = sorted(available_years[:n_years])

        # Calculate rainfall statistics
        rainfall_subset = rainfall[rainfall["year"].isin(years_sel)]
        rainfall_stats = (
            rainfall_subset.groupby(["state", "year"])["annual_rainfall_mm"]
            .mean()
            .reset_index()
            .sort_values(["year", "state"])
        )

        # Calculate average rainfall for answer
        avg_a = rainfall_subset[rainfall_subset["state"] == state_a]["annual_rainfall_mm"].mean()
        avg_b = rainfall_subset[rainfall_subset["state"] == state_b]["annual_rainfall_mm"].mean()

        # Filter agriculture data
        agri_subset = agri_df[agri_df["state"].isin([state_a, state_b])]
        agri_subset = agri_subset[agri_subset["year"].isin(years_sel)]

        # Apply crop filter if provided
        if crop_filter:
            agri_subset = agri_subset[agri_subset["crop"].str.contains(crop_filter, case=False, na=False)]

        # Rank crops by production
        crop_rankings = (
            agri_subset.groupby(["state", "crop"])["production_tonnes"]
            .sum()
            .reset_index()
        )
        crop_rankings["rank"] = crop_rankings.groupby("state")["production_tonnes"].rank(
            method="first", ascending=False
        )
        crop_rankings = crop_rankings[crop_rankings["rank"] <= top_m]
        crop_rankings = crop_rankings.sort_values(["state", "rank"])

        # Create rainfall table
        pivot = rainfall_stats.pivot(index="year", columns="state", values="annual_rainfall_mm")
        rainfall_rows = []
        for year in years_sel:
            row = [int(year)]
            for state in [state_a, state_b]:
                value = pivot.get(state, {}).get(year, None)
                row.append(float(round(float(value), 1)) if value is not None else None)
            rainfall_rows.append(row)

        rainfall_table = {
            "title": "Average annual rainfall (mm)",
            "headers": ["Year", state_a, state_b],
            "rows": rainfall_rows
        }

        # Create crop table
        crop_rows = []
        for state in [state_a, state_b]:
            subset = crop_rankings[crop_rankings["state"] == state]
            if subset.empty:
                crop_rows.append([state, "No data", "—"])
                continue
            for _, row in subset.iterrows():
                crop_rows.append([
                    state,
                    row["crop"],
                    float(round(float(row["production_tonnes"]), 2))
                ])

        crop_table = {
            "title": f"Top {top_m} crops by production" + (f" (filter: {crop_filter})" if crop_filter else ""),
            "headers": ["State", "Crop", "Production (tonnes)"],
            "rows": crop_rows
        }

        # Generate answer
        answer = (
            f"Compared rainfall for {state_a} and {state_b} over {len(years_sel)} year(s). "
            f"{state_a} averaged {avg_a:.1f} mm while {state_b} averaged {avg_b:.1f} mm."
        )
        if crop_filter:
            answer += f" Filtered crop category: {crop_filter}."

        # Citations
        citations = [
            {
                "dataset": "rainfall",
                "source": "https://data.gov.in/resources/rainfall-sub-division-wise-distribution",
                "resource_id": "cca5f77c-68b3-43df-bd01-beb3b69204ed"
            },
            {
                "dataset": "agriculture",
                "source": "https://data.gov.in/resources/district-wise-crop-production-statistics",
                "resource_id": "9ef84268-d588-465a-a308-a864a43d0070"
            }
        ]

        return {
            "answer": answer,
            "tables": [rainfall_table, crop_table],
            "citations": citations
        }


# Auto-register this plugin when module is imported
plugin_registry.register(CompareRainfallCropsPlugin())
