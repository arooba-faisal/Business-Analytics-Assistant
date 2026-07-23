# Business-Analytics-Assistant

## Project Overview
A working MVP built for the Business Analytics Assistant challenge. The application enables business owners to connect multiple data sources, ask questions in plain English, and receive actionable insights with automatically selected visualizations.

Designed for non-technical users, the system eliminates the need to write SQL or use complex BI tools by converting natural language into database queries and presenting results in an intuitive format.

## Features:
- Connect multiple data sources
- SQLite database
- CSV file upload
- Natural language querying
- Automatic SQL generation
- Adaptive chart selection based on returned data
- Plain-English insight generation
- Multi-branch analytics for restaurant businesses
- Cross-source querying across connected datasets

## Tech Stack:
### Backend
- Python
- Flask
- SQLite
- Pandas

### AI
- OpenAI GPT-5.5
- Claude Sonnet 5
- Lovable.ai

## Installation Steps

1. Clone the repository.

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

2. Create a virtual environment.

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required dependencies.

```bash
pip install -r requirements.txt
```

4. Create a `.env` file (or copy `.env.example`) and add your OpenAI API key.

```env
OPENAI_API_KEY=your_api_key
```

5. Generate the sample data.

```bash
python generate_data.py
```

This creates:

- `data/branches.db`
- `data/inventory.csv`

---

## How to Run the Project

Start the Flask application.

```bash
python app.py
```

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

### Demo Workflow

1. Connect the SQLite database.
2. Upload the provided `inventory.csv`.
3. Ask questions in plain English, for example:
   - Which branch had the lowest revenue last month?
   - Show daily revenue trends for the last 30 days.
   - Compare average order value across all branches.
   - Flag branches where footfall dropped more than 20% week-over-week.
   - Which inventory items are below their reorder level for the Faisalabad branch?

The system automatically:
- Converts the question into SQL
- Executes the query
- Selects the most appropriate visualization
- Generates a plain-English business insight

---

## AI Models Used

- **OpenAI GPT-5.5** – Natural language to SQL conversion and business insight generation.
- **Claude Sonnet 5** – Assisted with development, implementation, debugging, and code refinement during the project.

---

## Data Connectors Implemented

### SQLite Connector
Loads restaurant operational data including:
- Branches
- Sales
- Footfall

### CSV Connector

Allows users to upload inventory data, which is loaded into the shared in-memory database.
Both connectors are unified into a single in-memory SQLite database, enabling queries across multiple connected datasets.

---

## Known Limitations

- Currently supports only SQLite and CSV connectors.
- Requires an OpenAI API key to use natural language querying.
- Sample data is generated for demonstration purposes.
- Cross-source queries depend on compatible schemas between connected datasets.
- Visualization selection is rule-based and currently supports KPI cards, bar charts, line charts, pie charts, ranked tables, and geographic views where applicable.
- No user authentication or persistent storage of uploaded datasets.
  
## Project structure

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
