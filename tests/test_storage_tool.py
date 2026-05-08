"""Tests for StorageTool using an in-memory SQLite database."""

import pytest
from tools.storage_tool import StorageTool

SAMPLE_PROFILE = {
    "name": "TestUser",
    "age": 25,
    "gender": "male",
    "weight_kg": 80.0,
    "height_cm": 180.0,
    "activity_level": "moderate",
    "goal": "gain_muscle",
}

SAMPLE_MEAL = {
    "food_name": "chicken breast",
    "quantity_g": 200,
    "calories": 330,
    "protein_g": 62,
    "carbs_g": 0,
    "fat_g": 7.2,
    "notes": "post-workout",
}


@pytest.fixture
def storage(tmp_path):
    return StorageTool(db_path=str(tmp_path / "test.db"))


class TestUserProfile:
    def test_save_and_retrieve_profile(self, storage):
        storage.save_user_profile(SAMPLE_PROFILE)
        result = storage.get_user_profile("TestUser")
        assert result is not None
        assert result["name"] == "TestUser"
        assert result["weight_kg"] == 80.0

    def test_profile_not_found_returns_none(self, storage):
        assert storage.get_user_profile("Nobody") is None

    def test_update_profile(self, storage):
        storage.save_user_profile(SAMPLE_PROFILE)
        updated = {**SAMPLE_PROFILE, "weight_kg": 82.0}
        storage.save_user_profile(updated)
        result = storage.get_user_profile("TestUser")
        assert result["weight_kg"] == 82.0

    def test_missing_required_field_raises(self, storage):
        incomplete = {k: v for k, v in SAMPLE_PROFILE.items() if k != "age"}
        with pytest.raises(ValueError, match="Missing profile fields"):
            storage.save_user_profile(incomplete)


class TestMealLog:
    def test_log_meal_returns_id(self, storage):
        row_id = storage.log_meal(SAMPLE_MEAL)
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_multiple_meals_get_sequential_ids(self, storage):
        id1 = storage.log_meal(SAMPLE_MEAL)
        id2 = storage.log_meal(SAMPLE_MEAL)
        assert id2 > id1

    def test_missing_required_meal_field_raises(self, storage):
        incomplete = {k: v for k, v in SAMPLE_MEAL.items() if k != "calories"}
        with pytest.raises(ValueError, match="Missing meal entry fields"):
            storage.log_meal(incomplete)


class TestDailySummary:
    def test_empty_day_returns_zeros(self, storage):
        summary = storage.get_daily_summary("2099-12-31")
        assert summary["total_calories"] == 0
        assert summary["meals_logged"] == 0

    def test_summary_accumulates_meals(self, storage):
        meal = {**SAMPLE_MEAL, "logged_at": "2030-01-15T08:00:00"}
        storage.log_meal(meal)
        storage.log_meal(meal)
        summary = storage.get_daily_summary("2030-01-15")
        assert summary["meals_logged"] == 2
        assert summary["total_calories"] == pytest.approx(660, abs=0.1)
        assert summary["total_protein_g"] == pytest.approx(124, abs=0.1)

    def test_summary_only_counts_target_date(self, storage):
        storage.log_meal({**SAMPLE_MEAL, "logged_at": "2030-01-15T08:00:00"})
        storage.log_meal({**SAMPLE_MEAL, "logged_at": "2030-01-16T08:00:00"})
        summary = storage.get_daily_summary("2030-01-15")
        assert summary["meals_logged"] == 1


class TestMealHistory:
    def test_returns_list(self, storage):
        assert isinstance(storage.get_meal_history(), list)

    def test_history_limit_respected(self, storage):
        for _ in range(5):
            storage.log_meal(SAMPLE_MEAL)
        history = storage.get_meal_history(limit=3)
        assert len(history) == 3

    def test_most_recent_first(self, storage):
        storage.log_meal({**SAMPLE_MEAL, "food_name": "first", "logged_at": "2030-01-01T07:00:00"})
        storage.log_meal({**SAMPLE_MEAL, "food_name": "second", "logged_at": "2030-01-01T08:00:00"})
        history = storage.get_meal_history(limit=2)
        assert history[0]["food_name"] == "second"
