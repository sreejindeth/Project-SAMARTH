from __future__ import annotations
       
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .data_manager import DataManager
from .fuzzy_match import (
    fuzzy_match_in_dataframe,
    find_crop_with_synonyms,
    similarity_score,
)


@dataclass
class Table:
    title: str
    headers: List[str]
    rows: List[List]


@dataclass
class AnswerPayload:
    answer: str
    tables: List[Table] = field(default_factory=list)
    citations: List[Dict[str, str]] = field(default_factory=list)
    debug: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "answer": self.answer,
            "tables": [
                {"title": tbl.title, "headers": tbl.headers, "rows": tbl.rows} for tbl in self.tables
            ],
            "citations": self.citations,
            "debug": self.debug or {},
        }


class AnalyticsEngine:
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.agri = self.dm.load_dataset("agriculture")
        self.rainfall = self.dm.load_dataset("rainfall")
        self._normalise()

    def refresh(self):
        self.agri = self.dm.load_dataset("agriculture", force_refresh=True)
        self.rainfall = self.dm.load_dataset("rainfall", force_refresh=True)
        self._normalise()

    def _normalise(self):
        self.agri["state"] = self.agri["state"].str.title()
        self.agri["district"] = self.agri["district"].str.title()
        self.agri["crop"] = self.agri["crop"].str.title()
        self.agri["year"] = self.agri["year"].astype(int)
        self.agri["production_tonnes"] = self.agri["production_tonnes"].astype(float)

        self.rainfall["state"] = self.rainfall["state"].str.title()
        self.rainfall["year"] = self.rainfall["year"].astype(int)
        self.rainfall["annual_rainfall_mm"] = self.rainfall["annual_rainfall_mm"].astype(float)

    def _fuzzy_match_state(self, query_state: str, threshold: float = 0.75) -> Optional[str]:
        """
        Find the best matching state name using fuzzy matching.
        Checks both agriculture and rainfall datasets.
        """
        if not query_state:
            return None

        query_normalized = query_state.replace("_", " ").title()

        # Try exact match first
        if query_normalized in self.agri["state"].values:
            return query_normalized
        if query_normalized in self.rainfall["state"].values:
            return query_normalized

        # Try fuzzy match in agriculture data
        match_agri = fuzzy_match_in_dataframe(self.agri, "state", query_normalized, threshold)
        if match_agri:
            return match_agri

        # Try fuzzy match in rainfall data
        match_rain = fuzzy_match_in_dataframe(self.rainfall, "state", query_normalized, threshold)
        if match_rain:
            return match_rain

        return None

    def _fuzzy_match_crop(self, query_crop: str, threshold: float = 0.75) -> Optional[str]:
        """
        Find the best matching crop name using fuzzy matching and synonyms.
        """
        if not query_crop:
            return None

        query_normalized = query_crop.replace("_", " ").title()

        # Try exact match first
        if query_normalized in self.agri["crop"].values:
            return query_normalized

        # Try with synonyms and fuzzy matching
        return find_crop_with_synonyms(self.agri, "crop", query_normalized, threshold)

    def compare_rainfall_and_crops(
        self,
        state_a: str,
        state_b: str,
        crop_filter: Optional[str],
        last_n_years: Optional[int],
        top_m: int = 3,
    ) -> AnswerPayload:
        # Use fuzzy matching for states
        matched_state_a = self._fuzzy_match_state(state_a)
        matched_state_b = self._fuzzy_match_state(state_b)

        if not matched_state_a:
            raise ValueError(f"Could not find state matching '{state_a}'. Available states: {', '.join(self.rainfall['state'].unique())}")
        if not matched_state_b:
            raise ValueError(f"Could not find state matching '{state_b}'. Available states: {', '.join(self.rainfall['state'].unique())}")

        state_a, state_b = matched_state_a, matched_state_b

        rainfall = self.rainfall[self.rainfall["state"].isin([state_a, state_b])]
        available_years = sorted(rainfall["year"].unique(), reverse=True)
        if not available_years:
            raise ValueError("No rainfall data found for the requested states.")
        n_years = last_n_years or min(len(available_years), 5)
        years = sorted(available_years[:n_years])

        rainfall_subset = rainfall[rainfall["year"].isin(years)]
        rainfall_stats = (
            rainfall_subset.groupby(["state", "year"])["annual_rainfall_mm"]
            .mean()
            .reset_index()
            .sort_values(["year", "state"])
        )

        agri_subset = self.agri[self.agri["state"].isin([state_a, state_b])]
        agri_subset = agri_subset[agri_subset["year"].isin(years)]

        # Use fuzzy matching for crop filter
        if crop_filter:
            matched_crop = self._fuzzy_match_crop(crop_filter)
            if matched_crop:
                agri_subset = agri_subset[agri_subset["crop"] == matched_crop]
            else:
                # Fallback to partial string matching
                agri_subset = agri_subset[agri_subset["crop"].str.contains(crop_filter, case=False, na=False)]

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

        rainfall_table = Table(
            title="Average annual rainfall (mm)",
            headers=["Year", state_a, state_b],
            rows=self._pivot_rows(rainfall_stats, years, [state_a, state_b]),
        )

        crop_rows = []
        for state in [state_a, state_b]:
            subset = crop_rankings[crop_rankings["state"] == state]
            if subset.empty:
                crop_rows.append([state, "No data", "—"])
                continue
            for _, row in subset.iterrows():
                crop_rows.append(
                    [
                        state,
                        row["crop"],
                        float(round(float(row["production_tonnes"]), 2)),
                    ]
                )

        crop_table = Table(
            title=f"Top {top_m} crops by production" + (f" (filter: {crop_filter})" if crop_filter else ""),
            headers=["State", "Crop", "Production (tonnes)"],
            rows=crop_rows,
        )

        answer = (
            f"Compared rainfall for {state_a} and {state_b} over {len(years)} year(s). "
            f"{state_a} averaged {self._mean_for_state(rainfall_subset, state_a):.1f} mm "
            f"while {state_b} averaged {self._mean_for_state(rainfall_subset, state_b):.1f} mm."
        )
        if crop_filter:
            answer += f" Filtered crop category: {crop_filter}."

        citations = [
            self._citation("rainfall"),
            self._citation("agriculture"),
        ]
        return AnswerPayload(answer=answer, tables=[rainfall_table, crop_table], citations=citations)

    def district_extremes(
        self,
        state_a: str,
        state_b: str,
        crop: str,
        year: Optional[int],
    ) -> AnswerPayload:
        # Use fuzzy matching for states and crop
        matched_state_a = self._fuzzy_match_state(state_a)
        matched_state_b = self._fuzzy_match_state(state_b)
        matched_crop = self._fuzzy_match_crop(crop)

        if not matched_state_a:
            raise ValueError(f"Could not find state matching '{state_a}'. Available states: {', '.join(self.agri['state'].unique())}")
        if not matched_state_b:
            raise ValueError(f"Could not find state matching '{state_b}'. Available states: {', '.join(self.agri['state'].unique())}")
        if not matched_crop:
            raise ValueError(f"Could not find crop matching '{crop}'. Available crops: {', '.join(self.agri['crop'].unique())}")

        state_a, state_b, crop = matched_state_a, matched_state_b, matched_crop

        subset = self.agri[self.agri["crop"] == crop]
        if year:
            subset = subset[subset["year"] == year]
        if subset.empty:
            raise ValueError("No production data found for the requested crop/year.")

        latest_year = subset["year"].max()
        if not year:
            year = latest_year
        subset = subset[subset["year"] == year]

        state_a_rows = subset[subset["state"] == state_a]
        state_b_rows = subset[subset["state"] == state_b]

        rows = []
        parts = []

        if state_a_rows.empty:
            rows.append([state_a, "No records", "—"])
            parts.append(f"{state_a} did not report {crop} production in {year}.")
        else:
            max_row = state_a_rows.loc[state_a_rows["production_tonnes"].idxmax()]
            rows.append(
                [state_a, max_row["district"], float(round(float(max_row["production_tonnes"]), 2))]
            )
            parts.append(
                f"{state_a}'s peak output came from {max_row['district']} "
                f"with {max_row['production_tonnes']:.1f} tonnes."
            )

        if state_b_rows.empty:
            rows.append([state_b, "No records", "—"])
            parts.append(f"{state_b} did not report {crop} production in {year}.")
        else:
            min_row = state_b_rows.loc[state_b_rows["production_tonnes"].idxmin()]
            rows.append(
                [state_b, min_row["district"], float(round(float(min_row["production_tonnes"]), 2))]
            )
            parts.append(
                f"{state_b}'s lowest output was {min_row['district']} at {min_row['production_tonnes']:.1f} tonnes."
            )

        table = Table(
            title=f"District extremes for {crop} in {year}",
            headers=["State", "District", "Production (tonnes)"],
            rows=rows,
        )

        answer = " ".join(parts)

        citations = [self._citation("agriculture")]
        return AnswerPayload(answer=answer, tables=[table], citations=citations)

    def production_trend_with_climate(
        self,
        region: str,
        crop: str,
        years: Optional[int],
    ) -> AnswerPayload:
        # Use fuzzy matching for region and crop
        matched_region = self._fuzzy_match_state(region)
        matched_crop = self._fuzzy_match_crop(crop)

        if not matched_region:
            raise ValueError(f"Could not find region matching '{region}'. Available regions: {', '.join(self.agri['state'].unique())}")
        if not matched_crop:
            raise ValueError(f"Could not find crop matching '{crop}'. Available crops: {', '.join(self.agri['crop'].unique())}")

        region, crop = matched_region, matched_crop

        agri = self.agri[(self.agri["state"] == region) & (self.agri["crop"] == crop)]
        if agri.empty:
            raise ValueError("No production data found for the selected region/crop.")

        rainfall = self.rainfall[self.rainfall["state"] == region]
        if rainfall.empty:
            raise ValueError("No rainfall data found for the selected region.")

        years_available = sorted(agri["year"].unique(), reverse=True)
        n_years = years or min(len(years_available), 10)
        years_sel = sorted(years_available[:n_years])

        agri = agri[agri["year"].isin(years_sel)]
        rainfall = rainfall[rainfall["year"].isin(years_sel)]

        production_series = (
            agri.groupby("year")["production_tonnes"]
            .sum()
            .reset_index()
            .sort_values("year")
        )
        rainfall_series = rainfall.sort_values("year")[["year", "annual_rainfall_mm"]]

        merged = pd.merge(production_series, rainfall_series, on="year", how="inner")
        corr = merged["production_tonnes"].corr(merged["annual_rainfall_mm"])
        corr_text = self._interpret_correlation(corr)

        table = Table(
            title=f"{region} {crop} vs rainfall",
            headers=["Year", "Production (tonnes)", "Rainfall (mm)"],
            rows=[
                [
                    int(row["year"]),
                    float(round(float(row["production_tonnes"]), 2)),
                    float(round(float(row["annual_rainfall_mm"]), 1)),
                ]
                for _, row in merged.iterrows()
            ],
        )

        trend_pct = self._calc_growth(production_series)
        answer = (
            f"{region} recorded a {trend_pct:.1f}% change in {crop} production over {len(years_sel)} year(s). "
            f"Rainfall correlation indicates {corr_text} (r={corr:.2f})."
        )

        citations = [self._citation("agriculture"), self._citation("rainfall")]
        return AnswerPayload(answer=answer, tables=[table], citations=citations)

    def policy_arguments(
        self,
        region: str,
        crop_a: str,
        crop_b: str,
        years: Optional[int],
    ) -> AnswerPayload:
        # Use fuzzy matching for region and crops
        matched_region = self._fuzzy_match_state(region)
        matched_crop_a = self._fuzzy_match_crop(crop_a)
        matched_crop_b = self._fuzzy_match_crop(crop_b)

        if not matched_region:
            raise ValueError(f"Could not find region matching '{region}'. Available regions: {', '.join(self.agri['state'].unique())}")
        if not matched_crop_a:
            raise ValueError(f"Could not find crop matching '{crop_a}'. Available crops: {', '.join(self.agri['crop'].unique())}")
        if not matched_crop_b:
            raise ValueError(f"Could not find crop matching '{crop_b}'. Available crops: {', '.join(self.agri['crop'].unique())}")

        region, crop_a, crop_b = matched_region, matched_crop_a, matched_crop_b

        relevant = self.agri[self.agri["state"] == region]
        years_available = sorted(relevant["year"].unique(), reverse=True)
        n_years = years or min(len(years_available), 5)
        years_sel = sorted(years_available[:n_years])

        subset = relevant[relevant["year"].isin(years_sel)]

        agg = (
            subset[subset["crop"].isin([crop_a, crop_b])]
            .groupby(["crop", "year"])["production_tonnes"]
            .sum()
            .reset_index()
        )
        rainfall = (
            self.rainfall[(self.rainfall["state"] == region) & (self.rainfall["year"].isin(years_sel))]
            .sort_values("year")
        )

        insights = []
        tables = []

        for crop in [crop_a, crop_b]:
            crop_series = agg[agg["crop"] == crop].sort_values("year")
            if crop_series.empty:
                insights.append(f"No production records for {crop} in {region}.")
                continue
            growth = self._calc_growth(crop_series)
            avg_prod = crop_series["production_tonnes"].mean()
            insights.append(
                f"{crop}: avg {avg_prod:.1f} tonnes over {len(years_sel)} year(s) with {growth:.1f}% total change."
            )
            tables.append(
                Table(
                    title=f"{crop} production",
                    headers=["Year", "Production (tonnes)"],
                    rows=[
                        [int(row["year"]), float(round(float(row["production_tonnes"]), 2))]
                        for _, row in crop_series.iterrows()
                    ],
                )
            )

        if not rainfall.empty:
            avg_rain = rainfall["annual_rainfall_mm"].mean()
            trend = self._calc_growth(rainfall)
            insights.append(
                f"Rainfall averaged {avg_rain:.1f} mm with {trend:.1f}% change, "
                f"affecting water availability for {crop_b}."
            )
            tables.append(
                Table(
                    title="Rainfall context",
                    headers=["Year", "Rainfall (mm)"],
                    rows=[
                        [int(row["year"]), float(round(float(row["annual_rainfall_mm"]), 1))]
                        for _, row in rainfall.iterrows()
                    ],
                )
            )

        answer = (
            f"Supporting a shift towards {crop_a}: "
            + "; ".join(insights[:3])
        )

        citations = [self._citation("agriculture"), self._citation("rainfall")]
        return AnswerPayload(answer=answer, tables=tables, citations=citations)

    def _pivot_rows(self, df: pd.DataFrame, years: List[int], states: List[str]) -> List[List]:
        pivot = df.pivot(index="year", columns="state", values="annual_rainfall_mm")
        rows = []
        for year in years:
            row = [int(year)]
            for state in states:
                value = pivot.get(state, {}).get(year, None)
                row.append(float(round(float(value), 1)) if value is not None else None)
            rows.append(row)
        return rows

    @staticmethod
    def _mean_for_state(df: pd.DataFrame, state: str) -> float:
        subset = df[df["state"] == state]
        if subset.empty:
            return float("nan")
        return subset["annual_rainfall_mm"].mean()

    @staticmethod
    def _calc_growth(series: pd.DataFrame) -> float:
        series = series.sort_values(series.columns[0])
        values = series.iloc[:, -1].astype(float)
        if len(values) < 2 or values.iloc[0] == 0:
            return 0.0
        return ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100.0

    @staticmethod
    def _interpret_correlation(coefficient: float) -> str:
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

    def _citation(self, dataset: str) -> Dict[str, str]:
        meta = self.dm.get_metadata(dataset)
        return {
            "dataset": dataset,
            "source": meta.get("source_url", "https://data.gov.in"),
            "resource_id": meta.get("resource_id", ""),
        }
