A conversational business-intelligence agent for Skylark Drones leadership,

answering founder-level questions by querying live monday.com boards

(Work Orders + Deals) — no hardcoded data.



Live app: https://transcendent-sherbet-198577.netlify.app

Backend API: https://skylark-bi-agent-4v2e.onrender.com



> Note: the backend runs on Render's free tier and may take 30–50 seconds to respond to the first request after a period of inactivity (cold start).



Architecture:



\[ Browser (index.html) ]
       |  HTTP POST /chat
       v

\[ FastAPI backend (Render) ]

       |  tool-calling loop
       v

\[ Gemini 3.6 Flash ]  <-->  \[ query\_work\_orders / query\_deals tools ]

                                      |

                                      v

                         \[ monday.com GraphQL API ]

                         (Work Orders board, Deals board)





\- Frontend: single static index.html (vanilla JS + marked.js for

&#x20; markdown rendering), hosted on Netlify.

\- Backend: FastAPI, hosted on Render. Exposes one endpoint, POST /chat.

\- Agent: Google Gemini (`gemini-3.6-flash`) with two callable tools —

&#x20; query\_work\_orders and query\_deals — that fetch, flatten, and quality-

&#x20; annotate live data from monday.com before Gemini synthesizes an answer.

\- Data layer: monday\_client.py (raw GraphQL calls) + data\_utils.py (flattening + missing-data summarization).



See DECISION\_LOG.md for the reasoning behind these choices, trade-offs,

and known limitations.



Setup Instructions



1\. monday.com boards

&#x20;  - Create a monday.com account (or use an existing one).

&#x20;  - Import the provided CSVs (Deal funnel Data.xlsx, Work\_Order\_Tracker Data.xlsx) as two separate       boards named 'Deals' and 'Work Orders'.

&#x20;  - Go to your profile -> Developers -> My Access Tokens and generate an

&#x20;  API token with read access.

&#x20;  - Note the board IDs for both boards (visible in each board's URL, or via

&#x20;  a boards query — see monday\_client.get\_boards()).



2\. Backend

cd backend

python -m venv venv

venv\\Scripts\\activate        # Windows

pip install -r requirements.txt


Create a .env file in backend/ with:

MONDAY\_TOKEN=your\_monday\_api\_token

GOOGLE\_API\_KEY=your\_gemini\_api\_key

WORK\_ORDERS\_BOARD\_ID=your\_work\_orders\_board\_id

DEALS\_BOARD\_ID=your\_deals\_board\_id

Run locally:

python -m uvicorn main:app --reload

Visit 'http://127.0.0.1:8000/docs' to test the '/chat' endpoint directly.



3\. Frontend

Open frontend/index.html directly in a browser, or deploy it as a static

site (e.g. Netlify Drop). Update the `API\\\_URL` constant near the top of the <script> block to point at your backend's URL.



4\. Deployment (as used for this submission)

\- Backend: Render Web Service, Root Directory = backend,

&#x20; Build Command = pip install -r requirements.txt,

&#x20; Start Command = uvicorn main:app --host 0.0.0.0 --port $PORT,

&#x20; environment variables set in Render's dashboard (not committed to git).

\- Frontend: Netlify Drop (static file upload), API\\\_URL pointed at the deployed Render backend.



AI Tools Used

\- Claude (Anthropic) — used throughout for planning the architecture,

&#x20; writing and debugging backend/frontend code



Known Limitations

See DECISION\_LOG.md, section 7, for a full list of what would be improved with more time (name resolution for coded identifiers, stricter numeric/date validation, session persistence, caching, and automated tests).

