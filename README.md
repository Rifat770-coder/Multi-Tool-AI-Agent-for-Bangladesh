# Multi-Tool AI Agent for Bangladesh

**Live App:** [Bangladesh AI Agent](https://multi-tool-ai-agent-for-bangladesh.onrender.com/)

A LangChain agent, with a command-line interface and a simple Streamlit UI. It queries three Bangladesh datasets through three SQLite tools and uses Tavily for general knowledge. The main agent uses **LangChain AgentExecutor** and automatically chooses among exactly four tools.

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
bangladesh_agent/    Core application package
  agent.py          Four-tool agent and executor
  db_tools.py       Schema-aware SQLite tools
  web_tool.py       Tavily search tool
  validation.py     Shared question validation
scripts/
  convert_data.py   Verified CSV-to-SQLite conversion
tests/
  test_verification.py  Offline integration and UI checks
docs/
  DATA_LICENSES.md  Dataset attribution and permissions
  AUDIT_REPORT.md   Audit evidence and remaining actions
assets/             Logo, screenshot and ui.css
data/               Bundled databases, schema and source manifest
.github/            CI and contribution templates
.streamlit/         Streamlit configuration
app.py              Streamlit entry point
main.py             Interactive CLI entry point
convert_data.py     Converter compatibility entry point
verify.py           Offline suite compatibility entry point
requirements.txt    Direct dependencies
requirements.lock   Resolved dependency pins
.env.example        API-key configuration template
```

Run commands from the repository root. The root converter and test entry points retain the existing commands while their implementations live in `scripts/` and `tests/`.


## Installation and use

Use Python 3.13. Windows PowerShell:

```powershell
git clone https://github.com/Rifat770-coder/Multi-Tool-AI-Agent-for-Bangladesh.git
cd Multi-Tool-AI-Agent-for-Bangladesh
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
Copy-Item .env.example .env
python -m pip check
python verify.py
python main.py
# Or launch the UI:
python -m streamlit run app.py
```

macOS/Linux (commands provided; not locally executed):

```bash
git clone https://github.com/Rifat770-coder/Multi-Tool-AI-Agent-for-Bangladesh.git
cd Multi-Tool-AI-Agent-for-Bangladesh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
python -m pip check
python verify.py
python main.py
python -m streamlit run app.py
```

Before using the agent, edit `.env` with your own `OPENAI_API_KEY` and `TAVILY_API_KEY`. Obtain keys from [OpenAI](https://platform.openai.com/api-keys) and [Tavily](https://app.tavily.com/). Calls require network access and may cost money. Never commit `.env` or Streamlit secrets. Do not overwrite an existing `.env` when repeating setup. `OPENAI_MODEL` defaults to `gpt-4.1-mini` and must support tool calls and structured outputs.

The bundled databases need no download/rebuild. See [data rights and attribution](docs/DATA_LICENSES.md) before redistribution. Optional verified rebuild into a new directory:

```bash
python convert_data.py --output-dir .cache/rebuild
```

This checks pinned CSV SHA-256 values, schema conversion and database integrity. To replace the three bundled databases and schema manifest, explicitly run `python convert_data.py --overwrite`. Each database is replaced atomically, but the complete group is not one atomic transaction. Local cached CSVs must match the pinned hashes.

Type `exit` or `quit` to leave the CLI. Open http://localhost:8501 for the UI. Questions are limited to 2,000 characters.

![Bangladesh AI Agent interface](assets/Screenshot%202026-10-12%20223624.png)

## Available tools and example questions

| Tool | Purpose | Example |
|---|---|---|
| InstitutionsDBTool | Institution records and statistics | How many college records are in Dhaka? |
| HospitalsDBTool | Hospital/health organization records and statistics | How many hospitals are in Dhaka? |
| RestaurantsDBTool | Restaurant listings, ratings and address matches | How many restaurants are in Chittagong? |
| WebSearchTool | General knowledge through Tavily | What is the role of DGHS in Bangladesh? |

Each database tool receives a question, inspects the actual schema, generates SQL using the LLM, executes it against its assigned database and returns an answer grounded in the query results. Connections are read-only, SQLite authorization restricts queries to the assigned table, and execution/output limits prevent runaway queries. At most 200 result rows are returned; aggregate counts still cover all matching rows. The agent can request another query if a database query fails. General answers use search results and cite their source URLs.

## Verification, privacy and limitations

Run `python verify.py` without API keys. Tests use actual bundled database integrity/type/count checks, restricted SQL and execution interruption, scripted models for all four tool paths, mocked Tavily, input/setup failures and Streamlit AppTest submission/error checks. Scripted models prove integration, not live routing or factual accuracy.

The main question, tool observations (including query results and web excerpts) and intermediate conversation are sent to OpenAI. Database tools send the question, schema/category values to OpenAI for SQL planning, then question/SQL/results for prose. Mobile/contact columns can be selected and sent to OpenAI; no automatic redaction is claimed. Tavily receives search questions chosen by the model. Do not submit private data. Optional LangSmith tracing, if configured externally, can send traces to that service. No application analytics or persistent conversation storage is intentionally added.

Counts describe these records, not national totals. There is no deterministic Bangla-to-English location transliteration; matching depends on model SQL and recorded spellings. Universities are an explicit unsupported-category example. For restaurant ranking, specify rating descending, a minimum review count (for example 20) and address spellings; results remain dataset listings, not an independent ?best? recommendation.

On 2026-11-01 the published [Render demo](https://multi-tool-ai-agent-for-bangladesh.onrender.com/) returned HTTP 200 to a read-only request after about 22 seconds. That verifies availability of its HTML endpoint only, not live answers. No paid live API test or deployment is claimed. Detailed local results and remaining blockers are in [AUDIT_REPORT.md](docs/AUDIT_REPORT.md).

## Troubleshooting and maintenance

Missing keys: configure both values in `.env`. Missing databases: restore trusted bundled files or follow the verified rebuild path. Checksum mismatch: do not bypass verification; review upstream provenance before updating pins. API errors: check provider access, network and budget. A stale environment referencing a removed Python installation must be recreated. Preserve your `.env` separately.

`requirements.txt` declares direct dependencies; `requirements.lock` pins the resolved dependency graph for Python 3.13. Maintainers regenerate it with `uv pip compile requirements.txt -o requirements.lock --python 3.13`, install in a fresh environment, run `pip check`, `verify.py` and `pip-audit`. CI targets Windows/Linux Python 3.13; remote CI has not run as part of this local audit. See the audit report for the unresolved Pillow advisory constraint.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md). Code licensing and private reporting contacts require maintainer decisions. Public hosting must configure provider budgets/alerts and hosting access/rate controls; this app has no global rate limit or authentication.
