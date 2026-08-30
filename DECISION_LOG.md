1\. Integration Approach: MCP vs. API

The task allowed for the usage of either monday.com’s MCP server or its GraphQL API. My initial efforts were made with monday.com’s official MCP server (@mondaydotcomorg/monday-api-mcp) through npx, which ran successfully but required a MCP client (e.g. Claude Desktop, Cursor) to operate. To use the MCP server would have required an entire MCP client implementation (subprocess management and JSON-RPC handshake) and this is not an acceptable approach given the limited time available and the minor additional benefit over the use of the official REST/GraphQL API.



Final choice: Used monday.com's GraphQL API (https://api.monday.com/v2) with a lightweight Python client. This is in line with the requirements for the project of using “MCP or API — your choice” as well as the requirement of “Do not hardcode CSV data”, as all queries go live through the monday.com API.



2\. LLM Provider: Claude → Gemini

The agent was built using Anthropic's Claude API for tool-calling. Development was hindered by an issue with credit balance on a different Anthropic account, leaving no chance to purchase credits in time. Instead of stopping development, I moved the same tool-calling framework to Google's Gemini API

(gemini-3.6-flash), which has a free tier sufficient for this assignment.



Trade-off: The tool-calling loop is provider-agnostic as described in the previous paragraph — I have transferred the same architecture (system prompt + two callable tools + a response loop) with all changes just in SDK syntax. This is a benefit since switching to Claude, GPT, or another provider will require minimum effort in the future.



3\. Data Model \& Normalization

Raw monday.com API responses use internal column IDs (e.g. color\_mm6qf7gn) and every value is returned as text/value pairs. I built a flattening layer (data\_utils.py) that:

\- Maps column IDs to their human-readable titles

\- Converts empty strings to 'None' so missing data is explicit

\- Produces a per-query "data quality note" summarizing how much of each field is missing, so the agent can proactively caveat its answers.

Observed messiness in the real data:

\- All company/owner identifiers are anonymized codes (e.g.COMPANY089,

&#x20; OWNER\_001) with no name mapping available — the agent works with these codes directly rather than guessing real names.

\- Several columns (Expected Billing Month, Collection Date, etc.) are 0% populated across the entire Work Orders board — these are unused fields in this dataset, not per-row anomalies, so the agent is instructed to distinguish "structurally unused field" from "should be here but missing."

\- Close Date (A) on Deals is 100% missing, but this is expected given all sampled deals have Deal Status: Open — a naive missing-data flag would mislabel this as broken data. The agent's system prompt asks it to reason about why data is missing, not just report null counts.

\- All numeric fields (deal value, invoice amounts) are returned as text strings by the API and require casting before aggregation.



4\. Interpreting "Leadership Updates"

The optional requirement — "the agent shall assist in the creation of data to be used by the management in their updates" — was understood as: the agent must always answer concisely and executive-like (state the main point first, followed by 2-4 additional points) and not produce any raw data tables, irrespective of the nature of the question asked. This is ensured with the help of the system prompt, instead of using a separate dedicated function.



5\. Session/Conversation State

A basic in-memory session storage system was created (session\_id -> message history) in FastAPI. This storage system is intentionally basic: it resets when the server is restarted and does not work on multiple servers. Given that this was meant to be a prototype and that we are using free tier hosting (meaning a single server), it was an acceptable trade-off. The production version would use a database (such as Postgres or Redis) to store the sessions.



6\. Notable Debugging Challenges

\- The stale terminal-level environment variable MONDAY\_TOKEN=... in the terminal went unnoticed and replaced a successfully modified '.env' file because python-dotenv avoids overwriting any pre-existing elements in the environment. The problem was fixed by opening a new terminal.

\- The issue of the Anthropic "identity-linked" API key was that it required the presence of an explicit anthropic-workspace-id header which is not evident from the general error message.

\- '.env' file found its way into git by accident but it was prevented from going public thanks to GitHub's push protection measures. Just as a precaution, all credentials that appeared in the public domain had to be regenerated.

\- Initial Render deployment error happened because requirements.txt and backend sources were in the venv folder (which is as a matter of fact ignored by git) instead of in the backend's root — was fixed by moving those sources to their designated places and fixing the setting of Render's Root Directory.



7\. What I'd Do Differently With More Time

\- Instead of displaying raw company/owner codes, a proper code-to-name mapping layer should be added once it becomes available. 

\- When data is being ingested, attention must be paid to the fields being numeric or dates rather than trusting LLMs to deal with strings.

\- Caching should be implemented (for instance, use short TTLs in query\_work\_orders / query\_deals in order to limit the number of calls to monday.com API.

\- The session history must be saved in the database instead of being stored in the system memory.

\- Tests of normalization and quality summary should be performed, since these functions are the ones with the highest value in the context of correctness of the system. 

\- More time should be spent on the work and efforts related to the MCP path, since this is the direction of development of monday.com technology in the future.

