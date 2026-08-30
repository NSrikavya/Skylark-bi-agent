"""
The core conversational agent.
Uses Gemini with tool-calling (function calling): Gemini decides which
board(s) to query based on the founder's question, we fetch + clean the
data, then Gemini writes a natural-language answer grounded in that data.
"""
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from monday_client import get_board_items
from data_utils import flatten_board_items, summarize_data_quality

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

WORK_ORDERS_BOARD_ID = os.getenv("WORK_ORDERS_BOARD_ID")
DEALS_BOARD_ID = os.getenv("DEALS_BOARD_ID")

SYSTEM_PROMPT = """You are a business intelligence assistant for Skylark Drones' \
leadership team. You answer founder-level questions by querying two live \
monday.com boards: Work Orders (project execution + billing) and Deals \
(sales pipeline).

Rules:
- Always call the relevant tool(s) to get real data before answering. Never \
make up numbers.
- The data has real-world messiness: missing fields, numbers stored as text, \
and company/owner names replaced with codes (e.g. COMPANY089, OWNER_001) \
since no name mapping exists. Work with what's there.
- When missing data could affect your answer's accuracy (e.g. many deals \
missing a value field), say so explicitly and briefly.
- Be concise and executive-friendly: lead with the answer, then 1-3 \
supporting points. Avoid dumping raw rows unless asked.
- If a question is ambiguous (e.g. "this quarter" with no date given), \
state the assumption you're making rather than asking every time.
- Do not use strikethrough markdown formatting (~~text~~) to show revised \
or corrected numbers. Instead, state the correction in plain words, e.g. \
"initially appears as X, but excluding outliers this is actually Y."
"""

# --- Tool definitions, Gemini's function-calling format ---
query_work_orders_fn = types.FunctionDeclaration(
    name="query_work_orders",
    description=(
        "Fetch all Work Orders board items: project execution status, "
        "billing amounts, sector, dates, invoicing. Use for questions "
        "about operations, execution, billing, or delivery."
    ),
    parameters={"type": "object", "properties": {}},
)

query_deals_fn = types.FunctionDeclaration(
    name="query_deals",
    description=(
        "Fetch all Deals board items: sales pipeline, deal stage, value, "
        "sector, close dates. Use for questions about pipeline, sales, "
        "revenue forecasts, or deal status."
    ),
    parameters={"type": "object", "properties": {}},
)

tools = types.Tool(function_declarations=[query_work_orders_fn, query_deals_fn])


def run_tool(tool_name: str) -> dict:
    """Executes a tool call and returns a dict Gemini can read."""
    if tool_name == "query_work_orders":
        raw = get_board_items(WORK_ORDERS_BOARD_ID)
        flat = flatten_board_items(raw)
        quality_note = summarize_data_quality(flat["items"], "Work Orders")
        return {"items": flat["items"], "data_quality_note": quality_note}

    if tool_name == "query_deals":
        raw = get_board_items(DEALS_BOARD_ID)
        flat = flatten_board_items(raw)
        quality_note = summarize_data_quality(flat["items"], "Deals")
        return {"items": flat["items"], "data_quality_note": quality_note}

    return {"error": f"Unknown tool: {tool_name}"}


def ask_agent(user_message: str, conversation_history: list = None) -> str:
    """
    Sends a message to the agent, handling any tool calls Gemini makes
    along the way, and returns the final text answer.
    """
    contents = conversation_history[:] if conversation_history else []
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tools],
    )

    # Loop in case Gemini wants to call tools before answering
    while True:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        function_calls = [
            part.function_call
            for part in candidate.content.parts
            if part.function_call
        ]

        if function_calls:
            # Add Gemini's function-call turn to the conversation
            contents.append(candidate.content)

            # Run each requested tool and feed results back
            function_response_parts = []
            for fc in function_calls:
                result = run_tool(fc.name)
                function_response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )
            contents.append(types.Content(role="user", parts=function_response_parts))
            continue  # ask Gemini again with the tool results included

        # No more tools needed — extract the final text answer
        final_text = "".join(
            part.text for part in candidate.content.parts if part.text
        )
        return final_text


if __name__ == "__main__":
    print("Skylark BI Agent — type a question (or 'quit'):")
    history = []
    while True:
        q = input("\nYou: ")
        if q.lower() in ("quit", "exit"):
            break
        answer = ask_agent(q, history)
        print(f"\nAgent: {answer}")
        # NOTE: for simplicity this demo doesn't persist tool-call turns into
        # `history` across questions. Fine for testing; we'll improve this
        # when we wire it into FastAPI with proper session state.