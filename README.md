# Smart Fitness & Nutrition Agent

An AI-powered fitness and nutrition assistant that lets you track meals, calculate macros, and get personalised daily calorie targets — all through natural language.

**Test status:** 50 passed, 0 failed — `python -m pytest tests/ -v`

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 3. Run the assistant
python main.py
```

### Example prompts
```
I had a protein shake and 2 bananas for breakfast
Log 200g of chicken breast and 150g of white rice
What are my macros for today?
Calculate my daily calorie needs: 80kg, 180cm, 25 years old male, active, gain muscle
Show my recent meal history
```

### Running tests
```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
Smart-Fitness---Nutrition-Agent-master/
├── main.py                    # Interactive CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── agent/
│   └── fitness_agent.py       # FitnessAgent — Claude + tool-use orchestrator
├── tools/
│   ├── nutrition_tool.py      # NutritionLookupTool — calories/macros per food
│   ├── body_calc_tool.py      # BodyCalcTool — BMR, TDEE, macro targets
│   └── storage_tool.py        # StorageTool — SQLite meal log and user profile
├── config/
│   └── settings.py            # Environment variable loading
└── tests/
    ├── test_nutrition_tool.py  # 10 tests
    ├── test_body_calc_tool.py  # 13 tests
    ├── test_storage_tool.py    # 13 tests
    └── test_agent.py          # 14 tests (mocked Claude)
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from console.anthropic.com |
| `EDAMAM_APP_ID` | No | Edamam Nutrition API app ID (free tier) |
| `EDAMAM_APP_KEY` | No | Edamam Nutrition API key |
| `DATABASE_PATH` | No | Path to SQLite file (default: `fitness_data.db`) |
| `CLAUDE_MODEL` | No | Claude model ID (default: `claude-sonnet-4-6`) |

> Without Edamam credentials the system uses a built-in database of 20 common gym foods.

---

---

## Step 1 – Project Progress Journal (24.04.2026)

### 1. Short description of the planned system and its goal

My project is a Smart Fitness and Diet Assistant. Since I personally spend a lot of time at the gym and track my macros, I want to make this process easier. The goal is to create an AI agent where the user can just type something like "I had a protein shake and 2 bananas," and the system will automatically find the calories/macros and log them. Instead of searching a database manually, the AI will handle the "finding and calculating" part.

### 2. Description of the AI or agent-based approach

I will build a single intelligent agent using Python. The agent will act as a "brain." When a user sends a message, the AI will analyze the text to understand the intent. If it's about food, it will call a nutrition tool. If the user asks about their progress, it will look at the database. I plan to use the ReAct (Reasoning and Acting) logic so the agent can decide which step to take next depending on the user's input.

### 3. List of tools that will be used in the system

To make the system work, I will create at least three main tools:

**NutritionLookupTool:** This tool will connect to a web API (like Edamam or Nutritionix) to get real-time data about food (calories, protein, fats).

**BodyCalcTool:** A local Python tool that calculates the user's BMR (Basal Metabolic Rate) and daily needs using basic math formulas.

**StorageTool:** A simple module to save and read data from a local file (like a CSV or a small SQLite database) so the user can see their history.

### 4. Preliminary list of programming concepts required

For this project, I will need to use these concepts:

**OOP (Classes):** To keep my code organized by creating classes for the Agent and the Tools.

**API Requests:** I need to use the requests library to get data from the internet.

**Data Handling:** Working with JSON data (since APIs usually send JSON) and converting it into Python dictionaries.

**Error Handling:** Using try-except blocks so the program doesn't crash if the API is down or the user types something weird.

**Environment Variables:** Keeping my API keys safe in a .env file.

---

## Step 2 – Implementation Progress (08.05.2026)

### 1. Updated system description

The system was fully implemented as a command-line AI assistant. The user interacts through natural language typed in the terminal. The agent processes the message, decides which tool(s) to call, executes them, and returns a human-readable answer. A key design decision was to use Claude's native tool-use API (function calling) rather than manually parsing text, which makes the routing much more reliable.

The project is divided into four modules:
- `agent/fitness_agent.py` — orchestrates Claude and all tools
- `tools/nutrition_tool.py` — food nutrition lookup
- `tools/body_calc_tool.py` — body metric calculations
- `tools/storage_tool.py` — SQLite persistence
- `config/settings.py` — environment configuration
- `main.py` — CLI entry point

### 2. Programming concepts actually used

| Concept | Where it is applied |
|---|---|
| OOP (Classes) | `FitnessAgent`, `NutritionLookupTool`, `BodyCalcTool`, `StorageTool` — each is a class with a clear responsibility |
| API Requests | `NutritionLookupTool._try_edamam()` uses `requests.get()` with query parameters and a 10-second timeout |
| JSON handling | Claude's tool_use API passes inputs as dicts; tool results are serialised back with `json.dumps()` |
| Error handling | `try-except` in every tool; invalid inputs raise `ValueError` with a clear message; API failures fall back to local data |
| Environment variables | `python-dotenv` loads `.env` at startup; `config/settings.py` exposes typed constants |
| SQLite | `StorageTool` creates two tables (`user_profile`, `meal_log`) using `sqlite3`; uses parameterised queries to prevent SQL injection |
| Type hints | All function signatures use Python 3.11 type hints (`str | None`, `list[dict]`, etc.) |
| Mocking (unittest.mock) | Agent tests use `patch` to replace the Claude client and avoid real API calls |

### 3. How tools are integrated into the system

The integration follows the **tool-use (function calling)** pattern provided by the Anthropic Claude API:

1. Six tools are defined as JSON schemas in `TOOL_DEFINITIONS` inside `fitness_agent.py`.
2. Each message is sent to Claude together with those definitions.
3. Claude responds with either a final text answer (`stop_reason = "end_turn"`) or a tool call (`stop_reason = "tool_use"`).
4. When a tool call is received, `FitnessAgent._call_tool()` dispatches to the correct tool class method.
5. The tool result is serialised as JSON and appended to the conversation as a `tool_result` message.
6. Claude receives the result and continues reasoning — this loop repeats until Claude produces a text answer.

This means Claude decides *which* tool to use and *what parameters* to pass, based purely on the user's natural language message. No regex or keyword matching is needed.

**Data flow for "I had 200g of chicken breast":**
```
User message
  → Claude (decides to call lookup_nutrition)
    → NutritionLookupTool.lookup("chicken breast", 200)
      → Edamam API (or fallback DB) → {calories: 330, protein_g: 62, ...}
  → Claude (decides to call log_meal with those values)
    → StorageTool.log_meal({food_name: "chicken breast", ...})
  → Claude (generates final text summary)
→ User sees: "Logged 200g chicken breast — 330 kcal, 62g protein."
```

---

## Step 3 – Testing and Deployment (15.05.2026)

### 1. Testing process

Testing was done with **pytest** and runs alongside development. Each tool class has its own dedicated test file; the agent is tested separately using mocked Claude responses so no real API call or API key is required to run the test suite.

The test suite is run with:
```bash
python -m pytest tests/ -v
```

All **50 tests pass** in under 2 seconds.

### 2. Test scenarios

#### NutritionLookupTool (10 tests — `tests/test_nutrition_tool.py`)

| Scenario | What is verified |
|---|---|
| Known food lookup | Returns a dict with all required keys |
| Required keys | All of `food`, `quantity_g`, `calories`, `protein_g`, `carbs_g`, `fat_g`, `source` present |
| Quantity scaling | 200g returns exactly double the values of 100g |
| Partial name match | "protein shake" found via substring matching |
| Case insensitivity | "Banana" and "banana" return the same calories |
| Unknown food | Raises `ValueError` with helpful message |
| Empty food name | Raises `ValueError` |
| Zero quantity | Raises `ValueError` |
| Negative quantity | Raises `ValueError` |
| Source field | Is a non-empty string |

#### BodyCalcTool (13 tests — `tests/test_body_calc_tool.py`)

| Scenario | What is verified |
|---|---|
| Male BMR formula | 80kg/180cm/25yo male → 1805 kcal (Mifflin-St Jeor) |
| Female BMR formula | 60kg/165cm/30yo female → 1320.25 kcal |
| TDEE > BMR | After applying activity multiplier |
| Lose weight goal | Target calories 500 below TDEE |
| Gain muscle goal | Target calories 300 above TDEE |
| Maintain goal | Target calories equals TDEE |
| Macros present | protein_g, carbs_g, fat_g all in result |
| Protein per kg | Set to 2.0g per kg body weight |
| Carbs non-negative | Even in extreme deficit |
| Invalid gender | Raises `ValueError` |
| Weight too low | Raises `ValueError` |
| Invalid activity | Raises `ValueError` |
| Invalid goal | Raises `ValueError` |

#### StorageTool (13 tests — `tests/test_storage_tool.py`)

| Scenario | What is verified |
|---|---|
| Save and retrieve profile | Profile persisted and loaded correctly |
| Profile not found | Returns `None` |
| Update profile | Second save with same name overwrites |
| Missing profile field | Raises `ValueError` |
| Log meal returns ID | Integer row ID > 0 |
| Sequential meal IDs | Second entry ID > first |
| Missing meal field | Raises `ValueError` |
| Empty day summary | Returns zeros, not an error |
| Summary accumulates | Two meals → doubled totals |
| Summary date filter | Only counts entries on the target date |
| History returns list | Type check |
| History limit | Requesting 3 entries from 5 returns exactly 3 |
| Most recent first | Last logged meal appears at index 0 |

#### FitnessAgent (14 tests — `tests/test_agent.py`)

| Scenario | What is verified |
|---|---|
| Simple text response | Agent returns a string from Claude |
| Tool use: lookup_nutrition | Claude requests tool → tool called → result fed back → text returned |
| Tool use: log_meal | Full tool-use loop executes without error |
| Tool use: daily summary | get_daily_summary tool dispatched correctly |
| Reset clears history | `agent.reset()` empties conversation history |
| History grows | After one turn, history has 2 entries (user + assistant) |
| Unknown tool | `_call_tool` returns `{"error": ...}` instead of crashing |
| Dispatch lookup_nutrition | Correct return structure from real tool |
| Dispatch calculate_body_metrics | bmr > 0 in result |
| Dispatch log_meal | `success: True` in result |
| Dispatch daily summary | `total_calories` key present |
| Dispatch meal history | `entries` is a list |
| Dispatch save_user_profile | `success: True` |
| Tool error handling | Unknown food name → error dict, not exception |

### 3. Deployment preparation

The system is a local command-line application. A user can run it by following these steps:

```bash
# Clone the repository
git clone https://github.com/<your-username>/Smart-Fitness---Nutrition-Agent.git
cd Smart-Fitness---Nutrition-Agent

# Install dependencies (Python 3.11+ required)
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Open .env and paste your Anthropic API key

# Start the assistant
python main.py
```

The SQLite database file (`fitness_data.db`) is created automatically on first run. No database setup is required.

**Optional — Edamam API (free tier):**
Register at https://developer.edamam.com/ to get a free `app_id` and `app_key`. Add them to `.env` for real-time food data. Without them, the built-in fallback database of 20 common foods is used automatically.

### 4. Data conversion and porting

The system handles three data transformations:

**API response → internal dict:**
The Edamam API returns nested JSON with a `totalNutrients` object. `NutritionLookupTool._try_edamam()` extracts the relevant fields (`PROCNT`, `CHOCDF`, `FAT`) and scales them to a flat Python dict with rounded float values.

**Tool result → Claude message:**
Every tool result dict is serialised with `json.dumps()` before being inserted into the conversation as a `tool_result` content block. Claude receives it as a JSON string and interprets it naturally.

**Database row → Python dict:**
`StorageTool` uses `sqlite3` with named columns. Rows returned from queries are zipped with their column names to produce plain dicts, which are serialised to JSON for Claude.

### 5. Deployment strategy

For this project, **local command-line application** is the appropriate deployment model. Users install Python, set one environment variable, and run `python main.py`. The SQLite database keeps all data on the user's own machine.

For a production scenario, the system could be deployed as:

- **REST API (FastAPI):** Wrap `FitnessAgent.chat()` in a POST endpoint. Each request includes a session token to maintain conversation history. The SQLite database would be replaced with PostgreSQL.
- **Staged rollout:** Deploy to a staging environment first with a small group of beta users. Monitor tool call latency and API error rates before releasing to all users.
- **Environment management:** Use Docker to ensure consistent Python version and dependencies across machines. Secrets (API keys) are injected via environment variables, never committed to source control.
