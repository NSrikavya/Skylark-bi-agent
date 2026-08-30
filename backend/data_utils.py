"""
Utilities for turning monday.com's raw API response into clean,
flat Python dictionaries that are easy for both our code and the
LLM to reason about.
"""


def flatten_board_items(raw_response: dict) -> dict:
    """
    Takes the raw JSON from get_board_items() and returns:
    {
        "board_name": "Deals",
        "items": [
            {"id": "2848232703", "name": "Naruto", "Owner code": "OWNER_001", "Client Code": "COMPANY089", ...},
            ...
        ]
    }
    Uses column TITLES as keys (e.g. "Sector/service") instead of
    monday.com's internal column IDs (e.g. "color_mm6qf7gn"), so it's
    human-readable and easy for an LLM to work with.
    """
    board = raw_response["data"]["boards"][0]
    board_name = board["name"]

    # Build a lookup: column_id -> column_title
    column_id_to_title = {col["id"]: col["title"] for col in board["columns"]}

    flat_items = []
    for item in board["items_page"]["items"]:
        flat_item = {"id": item["id"], "name": item["name"]}
        for cv in item["column_values"]:
            title = column_id_to_title.get(cv["id"], cv["id"])
            text_value = cv["text"]
            # Normalize empty strings to None so missing data is explicit,
            # not silently treated as an empty-but-present value.
            flat_item[title] = text_value if text_value not in ("", None) else None
        flat_items.append(flat_item)

    return {"board_name": board_name, "items": flat_items}


def summarize_data_quality(flat_items: list, board_name: str) -> str:
    """
    Produces a short, human-readable note about how much data is missing
    per field. This is what lets our agent say things like:
    "Note: 8 of 45 deals are missing a Close Date, so this total may be incomplete."
    """
    if not flat_items:
        return f"{board_name}: no items found."

    total = len(flat_items)
    field_names = [k for k in flat_items[0].keys() if k not in ("id", "name")]

    missing_counts = {}
    for field in field_names:
        missing = sum(1 for item in flat_items if item.get(field) is None)
        if missing > 0:
            missing_counts[field] = missing

    if not missing_counts:
        return f"{board_name}: {total} items, no missing fields detected."

    lines = [f"{board_name}: {total} items total. Missing data:"]
    for field, count in sorted(missing_counts.items(), key=lambda x: -x[1]):
        pct = round((count / total) * 100)
        lines.append(f"  - {field}: {count}/{total} missing ({pct}%)")
    return "\n".join(lines)