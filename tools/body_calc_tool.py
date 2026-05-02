"""BodyCalcTool — calculates BMR, TDEE, and macro targets.

Uses the Mifflin-St Jeor equation for BMR and standard activity multipliers.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "lose_weight": -500,
    "maintain": 0,
    "gain_muscle": 300,
}


class BodyCalcTool:
    """Calculates BMR, TDEE, and personalised macro targets."""

    def calculate(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str,
        activity_level: str = "moderate",
        goal: str = "maintain",
    ) -> dict:
        """Return a dict with bmr, tdee, target_calories, and macro targets.

        Args:
            weight_kg: Body weight in kilograms.
            height_cm: Height in centimetres.
            age: Age in years.
            gender: 'male' or 'female'.
            activity_level: One of sedentary, light, moderate, active, very_active.
            goal: One of lose_weight, maintain, gain_muscle.

        Raises:
            ValueError: For out-of-range or invalid inputs.
        """
        self._validate(weight_kg, height_cm, age, gender, activity_level, goal)

        bmr = self._bmr(weight_kg, height_cm, age, gender)
        multiplier = ACTIVITY_MULTIPLIERS[activity_level]
        tdee = round(bmr * multiplier, 1)
        adjustment = GOAL_ADJUSTMENTS[goal]
        target_calories = round(tdee + adjustment, 1)

        protein_g = round(weight_kg * 2.0, 1)
        fat_g = round((target_calories * 0.25) / 9, 1)
        protein_cal = protein_g * 4
        fat_cal = fat_g * 9
        carbs_g = round((target_calories - protein_cal - fat_cal) / 4, 1)
        carbs_g = max(carbs_g, 0)

        return {
            "bmr": round(bmr, 1),
            "tdee": tdee,
            "target_calories": target_calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "activity_level": activity_level,
            "goal": goal,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bmr(self, weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        return base + 5 if gender.lower() == "male" else base - 161

    def _validate(self, weight_kg, height_cm, age, gender, activity_level, goal):
        if not (20 <= weight_kg <= 300):
            raise ValueError("weight_kg must be between 20 and 300")
        if not (100 <= height_cm <= 250):
            raise ValueError("height_cm must be between 100 and 250")
        if not (10 <= age <= 120):
            raise ValueError("age must be between 10 and 120")
        if gender.lower() not in ("male", "female"):
            raise ValueError("gender must be 'male' or 'female'")
        if activity_level not in ACTIVITY_MULTIPLIERS:
            raise ValueError(f"activity_level must be one of {list(ACTIVITY_MULTIPLIERS)}")
        if goal not in GOAL_ADJUSTMENTS:
            raise ValueError(f"goal must be one of {list(GOAL_ADJUSTMENTS)}")
