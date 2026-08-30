import os
import requests
from dotenv import load_dotenv

# Load the token from .env into the environment
load_dotenv()

MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_TOKEN = os.getenv("MONDAY_TOKEN")


def run_query(query: str, variables: dict = None) -> dict:
    """
    Sends a GraphQL query to monday.com and returns the JSON response.
    This is the one function everything else in our agent will use.
    """
    headers = {
        "Authorization": MONDAY_TOKEN,
        "Content-Type": "application/json",
        "API-Version": "2026-07",  # tells monday.com which API version to use
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(MONDAY_API_URL, json=payload, headers=headers)
    response.raise_for_status()  # will throw an error if something went wrong
    return response.json()


def get_boards():
    """Lists all boards in your account, with their IDs and names."""
    query = """
    {
      boards (limit: 25) {
        id
        name
      }
    }
    """
    return run_query(query)


def get_board_items(board_id: str):
    """
    Fetches all items (rows) from a board, including their column values.
    This is what we'll use to pull Work Orders and Deals data.
    """
    query = """
    query ($boardId: [ID!]) {
      boards (ids: $boardId) {
        name
        columns {
          id
          title
          type
        }
        items_page (limit: 100) {
          items {
            id
            name
            column_values {
              id
              text
              value
            }
          }
        }
      }
    }
    """
    variables = {"boardId": [board_id]}
    return run_query(query, variables)