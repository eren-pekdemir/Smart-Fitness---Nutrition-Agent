"""Tests for BodyCalcTool."""

import pytest
from tools.body_calc_tool import BodyCalcTool


@pytest.fixture
def tool():
    return BodyCalcTool()


class TestBMRCalculation:
    def test_male_bmr_formula(self, tool):
        # 80kg, 180cm, 25yo male → 10*80 + 6.25*180 - 5*25 + 5 = 1805
        result = tool.calculate(80, 180, 25, "male", "sedentary", "maintain")
        assert result["bmr"] == pytest.approx(1805.0, abs=0.5)

    def test_female_bmr_formula(self, tool):
        # 60kg, 165cm, 30yo female → 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
        result = tool.calculate(60, 165, 30, "female", "sedentary", "maintain")
        assert result["bmr"] == pytest.approx(1320.25, abs=0.5)

    def test_tdee_greater_than_bmr(self, tool):
        result = tool.calculate(75, 175, 28, "male", "moderate")
        assert result["tdee"] > result["bmr"]


class TestGoalAdjustment:
    def test_lose_weight_reduces_calories(self, tool):
        maintain = tool.calculate(75, 175, 28, "male", "moderate", "maintain")
        lose = tool.calculate(75, 175, 28, "male", "moderate", "lose_weight")
        assert lose["target_calories"] < maintain["target_calories"]

    def test_gain_muscle_increases_calories(self, tool):
        maintain = tool.calculate(75, 175, 28, "male", "moderate", "maintain")
        gain = tool.calculate(75, 175, 28, "male", "moderate", "gain_muscle")
        assert gain["target_calories"] > maintain["target_calories"]

    def test_maintain_equals_tdee(self, tool):
        result = tool.calculate(75, 175, 28, "male", "moderate", "maintain")
        assert result["target_calories"] == result["tdee"]


class TestMacroTargets:
    def test_macros_present(self, tool):
        result = tool.calculate(80, 180, 25, "male")
        for key in ("protein_g", "carbs_g", "fat_g"):
            assert key in result

    def test_protein_proportional_to_weight(self, tool):
        result = tool.calculate(80, 180, 25, "male")
        assert result["protein_g"] == pytest.approx(80 * 2.0, abs=0.5)

    def test_carbs_non_negative(self, tool):
        result = tool.calculate(40, 155, 20, "female", "sedentary", "lose_weight")
        assert result["carbs_g"] >= 0


class TestValidation:
    def test_invalid_gender_raises(self, tool):
        with pytest.raises(ValueError, match="gender"):
            tool.calculate(75, 175, 28, "other")

    def test_weight_too_low_raises(self, tool):
        with pytest.raises(ValueError, match="weight"):
            tool.calculate(10, 175, 28, "male")

    def test_invalid_activity_raises(self, tool):
        with pytest.raises(ValueError, match="activity"):
            tool.calculate(75, 175, 28, "male", activity_level="extreme")

    def test_invalid_goal_raises(self, tool):
        with pytest.raises(ValueError, match="goal"):
            tool.calculate(75, 175, 28, "male", goal="bulk")
