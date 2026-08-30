from monday_client import get_board_items
from data_utils import flatten_board_items, summarize_data_quality
import json
import os
from dotenv import load_dotenv

load_dotenv()

WORK_ORDERS_BOARD_ID = os.getenv("WORK_ORDERS_BOARD_ID")
DEALS_BOARD_ID = os.getenv("DEALS_BOARD_ID")

print("=== WORK ORDERS (flattened) ===")
raw_wo = get_board_items(WORK_ORDERS_BOARD_ID)
flat_wo = flatten_board_items(raw_wo)
print(f"Total items: {len(flat_wo['items'])}")
print(json.dumps(flat_wo["items"][:2], indent=2))  # just show first 2 for readability
print()
print(summarize_data_quality(flat_wo["items"], "Work Orders"))

print("\n\n=== DEALS (flattened) ===")
raw_deals = get_board_items(DEALS_BOARD_ID)
flat_deals = flatten_board_items(raw_deals)
print(f"Total items: {len(flat_deals['items'])}")
print(json.dumps(flat_deals["items"][:2], indent=2))
print()
print(summarize_data_quality(flat_deals["items"], "Deals"))