"""FitnessAgent — ReAct-style agent powered by Claude with tool use.

The agent exposes six tools to Claude:
  lookup_nutrition       — fetch calories/macros for a food item
  calculate_body_metrics — BMR, TDEE, and macro targets
  log_meal               — save a meal to the database
  get_daily_summary      — today's calorie/macro totals
  get_meal_history       — last N meal entries
  save_user_profile      — persist user bio data

Claude decides which tool(s) to call based on the user message and loops
until it produces a final text response (no more tool calls).
"""

import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL
from tools.nutrition_tool import NutritionLookupTool
from tools.body_calc_tool import BodyCalcTool
from tools.storage_tool import StorageTool

SYSTEM_PROMPT = """You are a smart fitness and nutrition assistant. You help users track their meals,
understand their nutritional intake, and calculate their daily energy needs.

When the user mentions food they ate, use lookup_nutrition to get the calories and macros,
then use log_meal to save it. Always confirm what was logged.

When asked about daily progress, use get_daily_summary. When asked about body metrics,
calorie needs, or macros, use calculate_body_metrics.

Be concise, friendly, and fitness-oriented. Show nutrition numbers clearly."""

TOOL_DEFINITIONS = [
    {
        "name": "lookup_nutrition",
        "description": "Look up calorie and macro data (protein, carbs, fat) for a food item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "food_name": {"type": "string", "description": "Name of the food item"},
                "quantity_grams": {"type": "number", "description": "Amount in grams (default 100)"},
            },
            "required": ["food_name"],
        },
    },
    {
        "name": "calculate_body_metrics",
        "description": "Calculate BMR, TDEE, and personalised daily macro targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "weight_kg": {"type": "number"},
                "height_cm": {"type": "number"},
                "age": {"type": "integer"},
                "gender": {"type": "string", "enum": ["male", "female"]},
                "activity_level": {
                    "type": "string",
                    "enum": ["sedentary", "light", "moderate", "active", "very_active"],
                },
                "goal": {
                    "type": "string",
                    "enum": ["lose_weight", "maintain", "gain_muscle"],
                },
            },
            "required": ["weight_kg", "height_cm", "age", "gender"],
        },
    },
    {
        "name": "log_meal",
        "description": "Save a meal entry to the user's log.",
        "input_schema": {
            "type": "object",
            "properties": {
                "food_name": {"type": "string"},
                "calories": {"type": "number"},
                "protein_g": {"type": "number"},
                "carbs_g": {"type": "number"},
                "fat_g": {"type": "number"},
                "quantity_g": {"type": "number"},
                "notes": {"type": "string"},
            },
            "required": ["food_name", "calories", "protein_g", "carbs_g", "fat_g"],
        },
    },
    {
        "name": "get_daily_summary",
        "description": "Get today's total calories and macros from the meal log.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format (omit for today)"},
            },
        },
    },
    {
        "name": "get_meal_history",
        "description": "Retrieve recent meal log entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of entries to return (default 10)"},
            },
        },
    },
    {
        "name": "save_user_profile",
        "description": "Save the user's profile (name, age, gender, weight, height, activity, goal).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "gender": {"type": "string", "enum": ["male", "female"]},
                "weight_kg": {"type": "number"},
                "height_cm": {"type": "number"},
                "activity_level": {
                    "type": "string",
                    "enum": ["sedentary", "light", "moderate", "active", "very_active"],
                },
                "goal": {
                    "type": "string",
                    "enum": ["lose_weight", "maintain", "gain_muscle"],
                },
            },
            "required": ["name", "age", "gender", "weight_kg", "height_cm", "activity_level", "goal"],
        },
    },
]


class FitnessAgent:
    """Orchestrates Claude + tools to answer fitness and nutrition queries."""

    def __init__(self, db_path: str | None = None):
        if not ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        kwargs = {"db_path": db_path} if db_path else {}
        self._nutrition = NutritionLookupTool()
        self._body_calc = BodyCalcTool()
        self._storage = StorageTool(**kwargs)
        self._history: list[dict] = []

    def chat(self, user_message: str) -> str:
        """Process a user message and return the assistant's response."""
        self._history.append({"role": "user", "content": user_message})

        while True:
            response = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self._history,
            )

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self._history.append({"role": "assistant", "content": response.content})
                return text

            if response.stop_reason == "tool_use":
                self._history.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._call_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                self._history.append({"role": "user", "content": tool_results})
                continue

            break

        return "I was unable to process your request. Please try again."

    def reset(self) -> None:
        """Clear conversation history."""
        self._history = []

    # ------------------------------------------------------------------
    # Tool dispatcher
    # ------------------------------------------------------------------

    def _call_tool(self, name: str, inputs: dict) -> dict:
        try:
            if name == "lookup_nutrition":
                return self._nutrition.lookup(
                    inputs["food_name"],
                    inputs.get("quantity_grams", 100.0),
                )
            if name == "calculate_body_metrics":
                return self._body_calc.calculate(
                    weight_kg=inputs["weight_kg"],
                    height_cm=inputs["height_cm"],
                    age=inputs["age"],
                    gender=inputs["gender"],
                    activity_level=inputs.get("activity_level", "moderate"),
                    goal=inputs.get("goal", "maintain"),
                )
            if name == "log_meal":
                row_id = self._storage.log_meal(inputs)
                return {"success": True, "meal_id": row_id}
            if name == "get_daily_summary":
                return self._storage.get_daily_summary(inputs.get("date"))
            if name == "get_meal_history":
                return {"entries": self._storage.get_meal_history(inputs.get("limit", 10))}
            if name == "save_user_profile":
                self._storage.save_user_profile(inputs)
                return {"success": True}
            return {"error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"error": str(exc)}

    def _extract_text(self, response) -> str:
        parts = [block.text for block in response.content if hasattr(block, "text")]
        return "\n".join(parts) if parts else ""
