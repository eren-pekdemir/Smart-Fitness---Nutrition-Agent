"""Tests for NutritionLookupTool."""

import pytest
from tools.nutrition_tool import NutritionLookupTool


@pytest.fixture
def tool():
    return NutritionLookupTool()


class TestNutritionLookupFallback:
    def test_known_food_returns_dict(self, tool):
        result = tool.lookup("banana", 100)
        assert isinstance(result, dict)

    def test_required_keys_present(self, tool):
        result = tool.lookup("banana", 100)
        for key in ("food", "quantity_g", "calories", "protein_g", "carbs_g", "fat_g", "source"):
            assert key in result, f"Missing key: {key}"

    def test_quantity_scaling(self, tool):
        result_100 = tool.lookup("chicken breast", 100)
        result_200 = tool.lookup("chicken breast", 200)
        assert abs(result_200["calories"] - result_100["calories"] * 2) < 0.1
        assert abs(result_200["protein_g"] - result_100["protein_g"] * 2) < 0.1

    def test_partial_name_match(self, tool):
        result = tool.lookup("protein shake", 30)
        assert result["calories"] > 0

    def test_case_insensitive(self, tool):
        r1 = tool.lookup("Banana", 100)
        r2 = tool.lookup("banana", 100)
        assert r1["calories"] == r2["calories"]

    def test_unknown_food_raises(self, tool):
        with pytest.raises(ValueError, match="Could not find"):
            tool.lookup("xyzzyzzyunknownfood999", 100)

    def test_empty_food_name_raises(self, tool):
        with pytest.raises(ValueError):
            tool.lookup("", 100)

    def test_zero_quantity_raises(self, tool):
        with pytest.raises(ValueError):
            tool.lookup("banana", 0)

    def test_negative_quantity_raises(self, tool):
        with pytest.raises(ValueError):
            tool.lookup("banana", -50)

    def test_source_field_is_string(self, tool):
        result = tool.lookup("oats", 100)
        assert isinstance(result["source"], str)
        assert len(result["source"]) > 0
