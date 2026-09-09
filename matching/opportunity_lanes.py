from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any


LANES = OrderedDict(
    [
        (
            "Systems & CRM",
            {
                "icon": "🧩",
                "title": [
                    "business systems", "systems analyst", "crm", "salesforce",
                    "dynamics", "applications analyst", "application analyst",
                    "systems administrator", "system administrator",
                ],
                "content": [
                    "dynamics 365", "dataverse", "power platform", "power automate",
                    "power apps", "salesforce", "crm", "system administration",
                    "security roles", "data model", "business systems",
                ],
            },
        ),
        (
            "Process & Continuous Improvement",
            {
                "icon": "⚙️",
                "title": [
                    "continuous improvement", "process analyst", "process improvement",
                    "operational excellence", "business process",
                ],
                "content": [
                    "continuous improvement", "process improvement", "process optimization",
                    "business process", "process mapping", "root cause", "lean",
                    "operational efficiency", "workflow improvement", "standard work",
                ],
            },
        ),
        (
            "Revenue Ops & Enablement",
            {
                "icon": "📈",
                "title": [
                    "revenue operations", "revops", "sales operations", "enablement",
                    "gtm operations", "go-to-market operations",
                ],
                "content": [
                    "revenue operations", "revops", "sales operations", "go-to-market",
                    "gtm", "sales enablement", "pipeline", "sales process", "funnel",
                    "quota", "forecasting", "salesforce",
                ],
            },
        ),
        (
            "BI & Insights",
            {
                "icon": "📊",
                "title": [
                    "business intelligence", "bi analyst", "data analyst", "insights analyst",
                    "analytics analyst", "reporting analyst", "performance analyst",
                ],
                "content": [
                    "power bi", "dax", "tableau", "dashboard", "business intelligence",
                    "data visualization", "reporting", "analytics", "insights", "sql",
                    "kpi", "metrics",
                ],
            },
        ),
        (
            "Pricing & Market Analytics",
            {
                "icon": "💹",
                "title": [
                    "pricing", "revenue management", "market analyst", "market analysis",
                    "commercial analytics", "market research", "revenue analyst",
                ],
                "content": [
                    "pricing", "revenue management", "market analysis", "market intelligence",
                    "commercial analytics", "pricing strategy", "competitive analysis",
                    "revenue optimization", "market research", "forecast",
                ],
            },
        ),
        (
            "Implementation & Applications",
            {
                "icon": "🛠️",
                "title": [
                    "implementation", "applications analyst", "application analyst",
                    "configuration analyst", "product support", "implementation consultant",
                ],
                "content": [
                    "implementation", "configuration", "application support", "rollout",
                    "user adoption", "requirements gathering", "requirements", "training",
                    "testing", "uat", "system implementation", "functional support",
                ],
            },
        ),
        (
            "Supply Chain & Procurement",
            {
                "icon": "📦",
                "title": [
                    "procurement", "sourcing", "supply chain", "logistics", "warehouse",
                    "wms", "purchasing", "commercialization", "vendor",
                ],
                "content": [
                    "procurement", "strategic sourcing", "sourcing", "supply chain",
                    "vendor", "warehouse", "wms", "inventory", "logistics", "purchasing",
                    "supplier", "commercialization",
                ],
            },
        ),
        (
            "Geospatial & Location Intelligence",
            {
                "icon": "🗺️",
                "title": ["gis", "geospatial", "geomatics", "mapping", "spatial"],
                "content": [
                    "gis", "geospatial", "arcgis", "spatial", "mapping", "geocoding",
                    "location intelligence", "latitude", "longitude", "geography",
                ],
            },
        ),
        (
            "Strategic Initiatives & Transformation",
            {
                "icon": "🧭",
                "title": [
                    "strategic initiatives", "business transformation", "transformation",
                    "strategy analyst", "integration analyst", "program analyst",
                ],
                "content": [
                    "strategic initiatives", "business transformation", "transformation",
                    "change management", "operating model", "integration", "strategy",
                    "cross-functional initiative", "program management",
                ],
            },
        ),
    ]
)

DEFAULT_LANE = "BI & Insights"


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _hits(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def classify_opportunity(
    job: dict[str, Any],
    profile: dict[str, Any],
    fit_score: int,
    fit_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify a role into a career lane without changing its fit score."""
    title = _normalize(job.get("title"))
    description = _normalize(job.get("description"))
    combined = f"{title} {description}"
    weights = profile.get("opportunity_lane_weights", {}) or {}

    results: list[tuple[float, int, str, list[str]]] = []
    for lane, config in LANES.items():
        title_hits = _hits(title, config["title"])
        content_hits = _hits(combined, config["content"])
        raw = (len(set(title_hits)) * 5) + (len(set(content_hits)) * 1.5)
        weighted = raw * float(weights.get(lane, 1.0) or 1.0)
        results.append((weighted, len(title_hits), lane, list(dict.fromkeys(title_hits + content_hits))))

    results.sort(key=lambda item: (item[0], item[1]), reverse=True)
    lane_score, _, lane, signals = results[0]
    if lane_score <= 0:
        lane = DEFAULT_LANE
        signals = []

    title_fit = int(((fit_details or {}).get("title") or {}).get("score", 0) or 0)
    verdict = str((fit_details or {}).get("verdict") or job.get("verdict") or "")
    hidden_threshold = int(profile.get("hidden_fit_threshold", 70) or 70)
    hidden_fit = bool(
        fit_score >= hidden_threshold
        and verdict != "SKIP"
        and title_fit < 24
        and lane_score >= 4.5
    )

    return {
        "lane": lane,
        "lane_icon": LANES[lane]["icon"],
        "lane_strength": round(float(lane_score), 1),
        "lane_signals": signals[:8],
        "hidden_fit": hidden_fit,
    }


def diversify_dataframe(df, bonus: float = 4.0):
    """Reorder strong jobs with a small first-seen lane bonus; scores remain untouched."""
    if df is None or getattr(df, "empty", True) or "opportunity_lane" not in df.columns:
        return df

    remaining = df.copy()
    ordered_indices: list[Any] = []
    seen_lanes: set[str] = set()

    while not remaining.empty:
        candidates = remaining.copy()
        candidates["_lane_bonus"] = candidates.apply(
            lambda row: bonus
            if row.get("opportunity_lane") not in seen_lanes and float(row.get("score", 0) or 0) >= 65
            else 0.0,
            axis=1,
        )
        candidates["_diverse_rank"] = candidates["score"].astype(float) + candidates["_lane_bonus"]
        sort_cols = ["_diverse_rank", "score"]
        ascending = [False, False]
        if "date_found" in candidates.columns:
            sort_cols.append("date_found")
            ascending.append(False)
        chosen_idx = candidates.sort_values(sort_cols, ascending=ascending).index[0]
        ordered_indices.append(chosen_idx)
        seen_lanes.add(str(remaining.loc[chosen_idx].get("opportunity_lane") or ""))
        remaining = remaining.drop(index=chosen_idx)

    return df.loc[ordered_indices].copy()
