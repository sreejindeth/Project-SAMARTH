"""
Production Trend Plugin

Analyzes production trend and correlates with climate/rainfall data.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from ..core.plugin_base import QueryPlugin, plugin_registry


class ProductionTrendPlugin(QueryPlugin):
    """
    Plugin for handling: "Production trend with climate correlation"

    Sample Prompt for THIS plugin (Project 2):
    "Analyze Paddy production trend in Maharashtra for last 5 years
     and its correlation with monsoon patterns."
    """

    @property
    def intent_name(self) -> str:
        return "production_trend_with_climate"

    @property
    def description(self) -> str:
        return "Analyze production trends correlated with climate"

    def can_handle(self, params: Dict[str, Any]) -> bool:
        """Check if we have required parameters."""
        required = ["region", "crop"]
        return all(params.get(key) for key in required)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters."""
        if not params.get("region"):
            return False, "Missing region parameter"
        if not params.get("crop"):
            return False, "Missing crop parameter"
        return True, None

    def execute(self, params: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Execute production trend query."""
        state = params["region"]
        crop = params["crop"]
        n_years = params.get("years", 10)

        agri_df = data["agriculture"]
        rainfall_df = data["rainfall"]

        # Filter agriculture data
        agri = agri_df[(agri_df["state"] == state) & (agri_df["crop"] == crop)]
        if agri.empty:
            raise ValueError("No production data found for the selected region/crop.")

        # Filter rainfall data
        rainfall = rainfall_df[rainfall_df["state"] == state]
        if rainfall.empty:
            raise ValueError("No rainfall data found for the selected region.")

        # Select years
        years_available = sorted(agri["year"].unique(), reverse=True)
        years_to_use = n_years if n_years else min(len(years_available), 10)
        years_sel = sorted(years_available[:years_to_use])

        agri = agri[agri["year"].isin(years_sel)]
        rainfall = rainfall[rainfall["year"].isin(years_sel)]

        # Aggregate production by year
        production_series = (
            agri.groupby("year")["production_tonnes"]
            .sum()
            .reset_index()
            .sort_values("year")
        )

        # Get rainfall data
        rainfall_series = rainfall.sort_values("year")[["year", "annual_rainfall_mm"]]

        # Merge data
        merged = pd.merge(production_series, rainfall_series, on="year", how="inner")

        # Calculate correlation
        corr = merged["production_tonnes"].corr(merged["annual_rainfall_mm"])
        corr_text = self._interpret_correlation(corr)

        # Create table
        table = {
            "title": f"{state} {crop} vs rainfall",
            "headers": ["Year", "Production (tonnes)", "Rainfall (mm)"],
            "rows": [
                [
                    int(row["year"]),
                    float(round(float(row["production_tonnes"]), 2)),
                    float(round(float(row["annual_rainfall_mm"]), 1))
                ]
                for _, row in merged.iterrows()
            ]
        }

        # Calculate growth trend
        trend_pct = self._calc_growth(production_series)

        # Generate answer
        answer = (
            f"{state} recorded a {trend_pct:.1f}% change in {crop} production over {len(years_sel)} year(s). "
            f"Rainfall correlation indicates {corr_text} (r={corr:.2f})."
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
            "tables": [table],
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

    @staticmethod
    def _interpret_correlation(coefficient: float) -> str:
        """Interpret correlation coefficient."""
        if np.isnan(coefficient):
            return "insufficient data for correlation"
        abs_coeff = abs(coefficient)
        if abs_coeff >= 0.7:
            level = "strong"
        elif abs_coeff >= 0.4:
            level = "moderate"
        else:
            level = "weak"
        direction = "positive" if coefficient > 0 else "negative"
        return f"{level} {direction} association"


# Auto-register this plugin
plugin_registry.register(ProductionTrendPlugin())
