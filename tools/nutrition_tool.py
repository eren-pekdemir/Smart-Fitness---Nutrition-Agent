"""NutritionLookupTool — fetches calorie and macro data for a food item.

Uses the Edamam Nutrition Analysis API when credentials are configured,
otherwise falls back to a built-in database of common gym foods.
"""

import requests
from config.settings import EDAMAM_APP_ID, EDAMAM_APP_KEY

EDAMAM_URL = "https://api.edamam.com/api/nutrition-data"

# Per-100g values: {name: {calories, protein, carbs, fat}}
FALLBACK_DB: dict[str, dict] = {
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23.0, "fat": 0.3},
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14.0, "fat": 0.2},
    "chicken breast": {"calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6},
    "whey protein": {"calories": 400, "protein": 80.0, "carbs": 8.0, "fat": 5.0},
    "protein shake": {"calories": 120, "protein": 25.0, "carbs": 5.0, "fat": 1.5},
    "oats": {"calories": 389, "protein": 17.0, "carbs": 66.0, "fat": 7.0},
    "white rice": {"calories": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3},
    "brown rice": {"calories": 112, "protein": 2.6, "carbs": 23.5, "fat": 0.9},
    "egg": {"calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0},
    "tuna": {"calories": 116, "protein": 25.5, "carbs": 0.0, "fat": 0.8},
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7.0, "fat": 0.4},
    "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20.0, "fat": 0.1},
    "peanut butter": {"calories": 588, "protein": 25.0, "carbs": 20.0, "fat": 50.0},
    "almonds": {"calories": 579, "protein": 21.0, "carbs": 22.0, "fat": 49.0},
    "greek yogurt": {"calories": 59, "protein": 10.0, "carbs": 3.6, "fat": 0.4},
    "milk": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3},
    "bread": {"calories": 265, "protein": 9.0, "carbs": 49.0, "fat": 3.2},
    "pasta": {"calories": 158, "protein": 5.8, "carbs": 31.0, "fat": 0.9},
    "salmon": {"calories": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0},
    "cottage cheese": {"calories": 98, "protein": 11.0, "carbs": 3.4, "fat": 4.3},
}


class NutritionLookupTool:
    """Retrieves calorie and macro data for a food item and quantity."""

    def lookup(self, food_name: str, quantity_grams: float = 100.0) -> dict:
        """Return nutrition data for `food_name` scaled to `quantity_grams`.

        Returns a dict with keys: food, quantity_g, calories, protein_g,
        carbs_g, fat_g, source.
        Raises ValueError if the food cannot be found in any source.
        """
        if not food_name or not isinstance(food_name, str):
            raise ValueError("food_name must be a non-empty string")
        if quantity_grams <= 0:
            raise ValueError("quantity_grams must be positive")

        result = self._try_edamam(food_name, quantity_grams)
        if result is None:
            result = self._try_fallback(food_name, quantity_grams)
        if result is None:
            raise ValueError(
                f"Could not find nutrition data for '{food_name}'. "
                "Try a more specific name or check the spelling."
            )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_edamam(self, food_name: str, quantity_grams: float) -> dict | None:
        if not EDAMAM_APP_ID or not EDAMAM_APP_KEY:
            return None
        try:
            ingr = f"{quantity_grams}g {food_name}"
            resp = requests.get(
                EDAMAM_URL,
                params={"app_id": EDAMAM_APP_ID, "app_key": EDAMAM_APP_KEY, "ingr": ingr},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            nutrients = data.get("totalNutrients", {})
            calories = data.get("calories", 0)
            if calories == 0:
                return None
            return {
                "food": food_name,
                "quantity_g": quantity_grams,
                "calories": round(calories, 1),
                "protein_g": round(nutrients.get("PROCNT", {}).get("quantity", 0), 1),
                "carbs_g": round(nutrients.get("CHOCDF", {}).get("quantity", 0), 1),
                "fat_g": round(nutrients.get("FAT", {}).get("quantity", 0), 1),
                "source": "Edamam API",
            }
        except Exception:
            return None

    def _try_fallback(self, food_name: str, quantity_grams: float) -> dict | None:
        key = food_name.strip().lower()
        entry = None
        if key in FALLBACK_DB:
            entry = FALLBACK_DB[key]
        else:
            for db_key, db_val in FALLBACK_DB.items():
                if db_key in key or key in db_key:
                    entry = db_val
                    break
        if entry is None:
            return None
        scale = quantity_grams / 100.0
        return {
            "food": food_name,
            "quantity_g": quantity_grams,
            "calories": round(entry["calories"] * scale, 1),
            "protein_g": round(entry["protein"] * scale, 1),
            "carbs_g": round(entry["carbs"] * scale, 1),
            "fat_g": round(entry["fat"] * scale, 1),
            "source": "local database",
        }
