from datetime import datetime

DATE_HINTS = ("date", "day", "month", "week", "period", "time")
CATEGORY_HINTS = ("branch", "city", "region", "item", "category", "product", "name", "menu")


def _is_date_like(value):
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m", "%d-%m-%Y"):
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
    return False


def infer_chart(rows: list[dict]) -> dict:
    """
    Returns {"chart_type": ..., "x_field": ..., "y_field": ..., "series_field": ...}
    chart_type is one of: kpi, bar, line, pie, table, geo
    """
    if not rows:
        return {"chart_type": "table", "reason": "No rows returned."}

    columns = list(rows[0].keys())
    numeric_cols = [c for c in columns if all(isinstance(r.get(c), (int, float)) for r in rows if r.get(c) is not None)]
    text_cols = [c for c in columns if c not in numeric_cols]

    date_col = next((c for c in text_cols if any(h in c.lower() for h in DATE_HINTS) or _is_date_like(rows[0].get(c))), None)
    category_col = next((c for c in text_cols if c != date_col and any(h in c.lower() for h in CATEGORY_HINTS)), None)
    geo_col = next((c for c in text_cols if c.lower() in ("city", "region")), None)

    # Single number, single row -> KPI scorecard
    if len(rows) == 1 and len(numeric_cols) == 1 and not date_col:
        return {
            "chart_type": "kpi",
            "y_field": numeric_cols[0],
            "reason": "Single aggregate value - best shown as a headline number.",
        }

    # Time series -> line chart
    if date_col and numeric_cols:
        return {
            "chart_type": "line",
            "x_field": date_col,
            "y_field": numeric_cols[0],
            "series_field": category_col,
            "reason": "A date/time dimension was detected - trend is best shown as a line chart.",
        }

    # Many categories, one metric, few rows -> pie (proportional share)
    if category_col and len(numeric_cols) == 1 and 2 <= len(rows) <= 8 and not date_col:
        # heuristic: if values look like they sum to a meaningful whole (shares), prefer pie
        # otherwise for >6 categories or 3+ metrics, prefer bar/table
        if geo_col:
            return {
                "chart_type": "geo",
                "location_field": geo_col,
                "y_field": numeric_cols[0],
                "reason": "Results are broken down by city/region - a geo view is most intuitive.",
            }
        return {
            "chart_type": "pie",
            "label_field": category_col,
            "y_field": numeric_cols[0],
            "reason": "Small number of categories with a single metric - proportional share is meaningful.",
        }

    # Multiple metrics or many rows -> ranked table
    if category_col and (len(numeric_cols) >= 2 or len(rows) > 8):
        return {
            "chart_type": "table",
            "label_field": category_col,
            "y_fields": numeric_cols,
            "reason": "Multiple metrics or many rows - a ranked table communicates this best.",
        }

    # Default: categorical comparison -> bar chart
    if category_col and numeric_cols:
        return {
            "chart_type": "bar",
            "x_field": category_col,
            "y_field": numeric_cols[0],
            "reason": "Comparing a metric across discrete categories - bar chart is clearest.",
        }

    return {"chart_type": "table", "reason": "Fallback - result shape did not match a specific visualization rule."}
