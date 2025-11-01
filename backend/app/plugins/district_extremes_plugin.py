"""
District Extremes Plugin

Finds districts with highest and lowest production for a specific crop.
"""
from typing import Dict, Any, Optional
import pandas as pd
from ..core.plugin_base import QueryPlugin, plugin_registry


class DistrictExtremesPlugin(QueryPlugin):
    """
    Plugin for handling: "Which districts had highest/lowest production?"

    Sample Prompt for THIS plugin (Project 2):
    "Which districts in Karnataka and Kerala had highest and lowest
     Sugarcane production in 2020?"
    """

    @property
    def intent_name(self) -> str:
        return "district_extremes"

    @property
    def description(self) -> str:
        return "Find districts with highest/lowest production"

    def can_handle(self, params: Dict[str, Any]) -> bool:
        """Check if we have required parameters."""
        required = ["state_a", "state_b", "crop"]
        return all(params.get(key) for key in required)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters."""
        if not params.get("state_a"):
            return False, "Missing state_a parameter"
        if not params.get("state_b"):
            return False, "Missing state_b parameter"
        if not params.get("crop"):
            return False, "Missing crop parameter"
        return True, None

    def execute(self, params: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Execute district extremes query."""
        state_a = params["state_a"]
        state_b = params["state_b"]
        crop = params["crop"]
        year = params.get("year")

        agri_df = data["agriculture"]

        # Filter by crop
        subset = agri_df[agri_df["crop"] == crop]

        # Filter by year if provided, otherwise use latest year
        if year:
            subset = subset[subset["year"] == year]

        if subset.empty:
            raise ValueError("No production data found for the requested crop/year.")

        latest_year = subset["year"].max()
        if not year:
            year = latest_year

        subset = subset[subset["year"] == year]

        # Get data for each state
        state_a_rows = subset[subset["state"] == state_a]
        state_b_rows = subset[subset["state"] == state_b]

        rows = []
        parts = []

        # Process state A (find max)
        if state_a_rows.empty:
            rows.append([state_a, "No records", "—"])
            parts.append(f"{state_a} did not report {crop} production in {year}.")
        else:
            max_row = state_a_rows.loc[state_a_rows["production_tonnes"].idxmax()]
            rows.append([
                state_a,
                max_row["district"],
                float(round(float(max_row["production_tonnes"]), 2))
            ])
            parts.append(
                f"{state_a}'s peak output came from {max_row['district']} "
                f"with {max_row['production_tonnes']:.1f} tonnes."
            )

        # Process state B (find min)
        if state_b_rows.empty:
            rows.append([state_b, "No records", "—"])
            parts.append(f"{state_b} did not report {crop} production in {year}.")
        else:
            min_row = state_b_rows.loc[state_b_rows["production_tonnes"].idxmin()]
            rows.append([
                state_b,
                min_row["district"],
                float(round(float(min_row["production_tonnes"]), 2))
            ])
            parts.append(
                f"{state_b}'s lowest output was {min_row['district']} "
                f"at {min_row['production_tonnes']:.1f} tonnes."
            )

        # Create table
        table = {
            "title": f"District extremes for {crop} in {year}",
            "headers": ["State", "District", "Production (tonnes)"],
            "rows": rows
        }

        # Generate answer
        answer = " ".join(parts)

        # Citations
        citations = [{
            "dataset": "agriculture",
            "source": "https://data.gov.in/resources/district-wise-crop-production-statistics",
            "resource_id": "9ef84268-d588-465a-a308-a864a43d0070"
        }]

        return {
            "answer": answer,
            "tables": [table],
            "citations": citations
        }


# Auto-register this plugin
plugin_registry.register(DistrictExtremesPlugin())
