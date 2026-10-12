### Simple UI

![Bangladesh AI Agent interface](assets/Screenshot%202026-10-12%20223624.png)

# Multi-Tool AI Agent for Bangladesh

A minimal LangChain agent for the Module 22 assignment, with a command-line interface and a simple Streamlit UI. It queries three Bangladesh datasets through three SQLite tools and uses Tavily for general knowledge. The main agent uses **LangChain AgentExecutor** and automatically chooses among exactly four tools.

## Dataset sources

| Database / table | Hugging Face dataset | Original CSV |
|---|---|---|
| `institutions.db` / `institutions` | [Institutional Information of Bangladesh](https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh) | `data.csv` |
| `hospitals.db` / `hospitals` | [All Bangladeshi Hospitals](https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals) | `all-bangladesh-hosptals.csv` |
| `restaurants.db` / `restaurants` | [Bangladeshi Restaurant Data](https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data) | `restaurants.csv` |

The converter downloads only these CSVs, normalizes column names to lowercase with underscores, and preserves every record. Identifiers/contact fields remain TEXT. Numeric fields use INTEGER or REAL where appropriate; empty numeric cells become NULL, while text cells retain their original text. `data/schema.json` documents the original-to-SQLite column mapping, types, source URLs and row counts. Import verification compares every converted record and checks SQLite integrity.

Actual fields and limitations:

- Institutions: 34,901 records; institute name/type, EIIN, division/district/thana/union/mauza identifiers and names, address, post, management, mobile, education level, affiliation and MPO status. Recorded types are Madrasha, College, School, Technical and Vocational, and School and College. **No University category is present**, so the university example cannot establish university coverage or national totals.
- Hospitals: 38,886 records; name, Bangla name, code, agency, type, division, district, city corporation, upazila, paurasava, union and private status. **No beds, doctors or facilities columns.** Records include health offices and other organizations, so a hospital-only count needs a stated type filter.
- Restaurants: 12,703 records; place ID, name, latitude, longitude, rating, number of reviews, affluence and address. **No cuisine column or separate city field.** Address matching measures dataset listings; some listings are shops or unrelated places. Rating zero is preserved, without assuming its meaning.

Counts describe dataset records, not nationwide totals. Geographic matches depend on recorded spelling (for example Chittagong/Chattogram) and address completeness. Missing information is reported instead of being invented or filled from web search.

## Technologies and files

Python 3.10–3.13 recommended, SQLite (Python standard library), LangChain Classic (`AgentExecutor`), LangChain OpenAI (`ChatOpenAI`), Tavily Search API (through Python's standard HTTP library), python-dotenv and Streamlit. AgentExecutor is provided by `langchain-classic`, as explained in the [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1). The search request follows the [Tavily Search API documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search).

```text
main.py             Interactive CLI
app.py              Simple Streamlit question-and-answer UI
agent.py            Tool-calling agent and AgentExecutor
convert_data.py     Download CSVs, infer types, build and verify databases
db_tools.py         Three schema-aware database tools
web_tool.py         Tavily WebSearchTool
verify.py           Offline database, tool and executor integration checks
requirements.txt    Dependencies
.env.example        API-key configuration template
data/               Three SQLite databases and schema.json
```

## Installation and use

1. Clone your submitted GitHub repository and enter its directory:

   ```bash
   git clone <your-github-repository-url>
   cd <your-repository-folder>
   ```

2. Create an environment and install dependencies:

   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell), then set `OPENAI_API_KEY` and `TAVILY_API_KEY`. Obtain your own credentials from [OpenAI](https://platform.openai.com/api-keys) and [Tavily](https://app.tavily.com/). `OPENAI_MODEL` defaults to `gpt-4.1-mini`; use a tool-calling and structured-output capable model available to your account. Calls require network access and may incur provider charges. Never commit `.env`.

4. Build the databases:

   ```bash
   python convert_data.py
   ```

   Bundled databases are immediately usable. Running conversion downloads CSVs when missing and rebuilds only the three assignment tables. Existing local `data/institutions.csv`, `data/hospitals.csv` and `data/restaurants.csv` are reused. Only use the specified sources. Failed downloads should be retried; never replace them with sample data.

5. Run the CLI:

   ```bash
   python main.py
   ```

   Enter questions repeatedly; type `exit` or `quit` to finish.

### Simple UI

![Bangladesh AI Agent interface](assets/Screenshot%202026-10-12%20223624.png)

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`, write a question and click **Ask**. The UI uses the same four-tool agent and `.env` configuration. It shows a loading indicator, the answer and a short message when a request fails. With the virtual environment activated, `streamlit run app.py` also works.

## Available tools and example questions

| Tool | Purpose | Example |
|---|---|---|
| InstitutionsDBTool | Institution records and statistics | How many universities are in Dhaka? |
| HospitalsDBTool | Hospital/health organization records and statistics | How many hospitals are in Dhaka? |
| RestaurantsDBTool | Restaurant listings, ratings and address matches | How many restaurants are in Chittagong? |
| WebSearchTool | General knowledge through Tavily | What is the role of DGHS in Bangladesh? |

Each database tool receives a question, inspects the actual schema, generates SQL using the LLM, executes it against its assigned database and returns an answer grounded in the query results. Connections are read-only, SQLite authorization restricts queries to the assigned table, and execution/output limits prevent runaway queries. At most 200 result rows are returned; aggregate counts still cover all matching rows. The agent can request another query if a database query fails. General answers use search results and cite their source URLs.

## Verification and submission

```bash
python verify.py
```

Offline checks exercise all three actual databases, schema/type checks, restricted SQL, missing-field handling and all four tool/executor paths using scripted model responses and a mocked Tavily response. These tests verify integration, **not live LLM routing accuracy or real web search**.

Completed local verification: all five offline tests passed, Python compilation passed, and conversion compared every imported record against its CSV input with successful SQLite integrity checks. The local test environment used Python 3.14.3 with existing installed packages; LangChain emits a Pydantic-v1 compatibility warning there, so Python 3.10–3.13 is recommended for setup. `OPENAI_API_KEY` and `TAVILY_API_KEY` were absent, so live API calls and live model routing remain unverified.

For live verification, configure both API keys, run `python main.py` and ask all four example questions. Check the selected tool via `agent.invoke({'input': question})` with `return_intermediate_steps=True` on the executor when debugging, then inspect `intermediate_steps`. Confirm database answers match SQL results and web answers cite actual returned URLs. No successful live verification is claimed without credentials.

Upload the code, README, requirements, `.env.example`, `data/schema.json` and three `.db` files to your GitHub repository; submit its URL. CSV downloads, `.env`, virtual environments and bytecode are excluded by `.gitignore`. No remote repository is created by the local setup instructions.
