# Business-Analytics-Assistant
A working MVP built for the Business Analytics Assistant challenge. The application enables business owners to connect multiple data sources, ask questions in plain English, and receive actionable insights with automatically selected visualizations.

Designed for non-technical users, the system eliminates the need to write SQL or use complex BI tools by converting natural language into database queries and presenting results in an intuitive format.

Features:
- Connect multiple data sources
- SQLite database
- CSV file upload
- Natural language querying
- Automatic SQL generation
- Adaptive chart selection based on returned data
- Plain-English insight generation
- Multi-branch analytics for restaurant businesses
- Cross-source querying across connected datasets

## 1. Project structure

```
nyrix-hackathon/
├── app.py              # Flask backend (routes/connectors/query)
├── nl_engine.py         # question -> SQL -> insight (OpenAI calls)
├── chart_logic.py        # rule-based chart-type inference
├── generate_data.py       # builds the sample multi-branch dataset
├── requirements.txt
├── .env.example          # copy to .env and paste your key
├── data/
│   ├── branches.db       # Connector 1: SQLite (branches, sales, footfall)
│   └── inventory.csv     # Connector 2: CSV (stock per branch/item)
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## 2. Setup in VS Code

1. Open this folder in VS Code (`File → Open Folder`).
2. Open a terminal in VS Code (`` Ctrl+` ``) and create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set your API key:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your **new, rotated** OpenAI key:
   ```
   OPENAI_API_KEY=sk-...your-new-key...
   ```
4. Generate the sample data (only needed once, already done, but re-run
   any time you want to regenerate it):
   ```bash
   python3 generate_data.py
   ```
   This creates `data/branches.db` (6-branch food chain, 3 months of daily
   sales + footfall) and `data/inventory.csv` (stock levels per branch).

## 3. Run it

```bash
python3 app.py
```

Open **http://127.0.0.1:5000** in your browser.

## 4. Demo flow

1. **Connect sources** — click "Connect SQLite" then "Connect CSV"(choose `data/inventory.csv` in the file picker, or upload your own CSV with the same columns). Both connectors load into one shared in-memory database, which is what lets a single question span both sources.
2. **Ask questions** — type your own, or click a suggestion chip:
   - *"Which of my branches had the lowest revenue last month?"* → bar chart
   - *"Show me daily revenue trend for the last 30 days across all branches."* → line chart
   - *"Compare average order value across all locations this quarter."* → bar/table
   - *"Flag any branch where footfall dropped more than 20% week-over-week."* → table/insight (the data has a real, deliberate footfall crash at the Faisalabad branch in the last two weeks, so this returns something real)
   - *"Which items in the inventory are below their reorder level for the Faisalabad branch?"* → **cross-source** query (joins the CSV inventory table with branch names from the SQLite source) — use this one to show off the bonus points
3. **Architecture walkthrough** (talking points for the 4–5 min mark):
   - Both connectors normalize into one shared SQLite schema in memory, so the LLM only ever reasons about one schema and can naturally JOIN across sources.
   - `nl_engine.py` turns the question into a single read-only `SELECT`(the SQL is guarded — no INSERT/UPDATE/DELETE/DROP allowed).
   - `chart_logic.py` is **rule-based, not another LLM call** — it looks at the shape of the result set (date column? category column? one row? one number? how many rows?) and picks kpi / bar / line / pie / table / geo. This is deterministic and fast, and you can point at the code during judging to show the actual decision logic.
   - A second, small LLM call turns the result rows into a 1–2 sentence plain-English insight.

## 5. Troubleshooting

- `OPENAI_API_KEY is not set` → you skipped step 2.3, or forgot to restart `python3 app.py` after editing `.env`.
- `branches.db not found` → run `python3 generate_data.py` from the project root first.
- CORS/blank page → make sure you're opening `http://127.0.0.1:5000` (the Flask URL), not opening `static/index.html` directly as a file.
