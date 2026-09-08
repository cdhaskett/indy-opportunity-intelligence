from __future__ import annotations

from io import BytesIO
import re
from typing import Any

import pandas as pd


COLUMN_ALIASES = {
    "company": [
        "company", "employer", "organization", "organisation", "company name",
        "employer name", "organization name",
    ],
    "title": [
        "title", "job title", "role", "position", "position title", "job",
    ],
    "date_applied": [
        "date applied", "applied date", "application date", "date", "submitted date",
        "date submitted", "application submitted",
    ],
    "status": [
        "status", "application status", "stage", "outcome", "application stage",
    ],
    "requisition_id": [
        "requisition id", "req id", "req", "job id", "posting id", "requisition",
        "reference id", "reference number",
    ],
    "source": [
        "source", "job board", "platform", "application source", "site",
    ],
    "url": [
        "url", "link", "job url", "posting url", "application url",
    ],
}


def _key(value: str | None) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _clean_cell(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _column_map(columns) -> dict[str, str]:
    normalized = {_key(str(column)): str(column) for column in columns}
    result: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            source = normalized.get(_key(alias))
            if source is not None:
                result[canonical] = source
                break
    return result


def read_application_file(data: bytes, filename: str) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    """Parse a CSV or XLSX application-history file into the app's history schema."""
    lower = (filename or "").lower()
    if lower.endswith(".xlsx"):
        frame = pd.read_excel(BytesIO(data), engine="openpyxl")
    elif lower.endswith(".csv"):
        try:
            frame = pd.read_csv(BytesIO(data), encoding="utf-8-sig")
        except UnicodeDecodeError:
            frame = pd.read_csv(BytesIO(data), encoding="latin-1")
    else:
        raise ValueError("Please upload a .csv or .xlsx file.")

    if frame.empty:
        raise ValueError("The file does not contain any application rows.")

    mapping = _column_map(frame.columns)
    if "company" not in mapping:
        raise ValueError(
            "I couldn't find a company/employer column. Rename that column to Company or Employer and try again."
        )

    rows: list[dict[str, Any]] = []
    skipped: list[str] = []

    for index, source_row in frame.iterrows():
        company = _clean_cell(source_row.get(mapping["company"]))
        if not company:
            skipped.append(f"Row {index + 2}: missing company")
            continue

        record: dict[str, Any] = {"company": company}
        for canonical in ["title", "status", "requisition_id", "source", "url"]:
            column = mapping.get(canonical)
            if column:
                value = _clean_cell(source_row.get(column))
                if value:
                    record[canonical] = value

        date_column = mapping.get("date_applied")
        if date_column:
            raw_date = source_row.get(date_column)
            if raw_date is not None and not pd.isna(raw_date):
                parsed = pd.to_datetime(raw_date, errors="coerce")
                if pd.notna(parsed):
                    record["date_applied"] = parsed.date().isoformat()
                else:
                    value = _clean_cell(raw_date)
                    if value:
                        record["date_applied"] = value

        rows.append(record)

    if not rows:
        raise ValueError("No usable application rows were found in that file.")

    return rows, mapping, skipped


def merge_application_history(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Merge imported rows without duplicating the same company/title/requisition combination."""
    merged = list(existing)
    seen: set[tuple[str, str, str]] = set()

    def signature(row: dict[str, Any]) -> tuple[str, str, str]:
        return (
            _key(str(row.get("company") or "")),
            _key(str(row.get("title") or "")),
            _key(str(row.get("requisition_id") or row.get("external_id") or "")),
        )

    for row in merged:
        seen.add(signature(row))

    added = 0
    for row in incoming:
        sig = signature(row)
        if sig in seen:
            continue
        merged.append(row)
        seen.add(sig)
        added += 1

    return merged, added
