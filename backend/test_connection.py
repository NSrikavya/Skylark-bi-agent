import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("MONDAY_TOKEN")
print("Token repr:", repr(token))
print("Token length:", len(token) if token else 0)

from monday_client import get_boards

print("Testing connection to monday.com...")
result = get_boards()
print(result)