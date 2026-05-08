"""Integration tests for FitnessAgent using mocked Claude responses.

These tests verify the agent's tool-dispatching logic without making real API calls.
"""

import json
import pytest
from unittest.mock import MagicMock, patch


def _make_text_response(text: str):
    """Build a mock Claude response that ends with a text block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_use_response(tool_name: str, tool_id: str, inputs: dict):
    """Build a mock Claude response that requests a tool call."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = tool_name
    block.input = inputs
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [block]
    return response


@pytest.fixture
def agent(tmp_path):
    with patch("agent.fitness_agent.ANTHROPIC_API_KEY", "test-key"):
        with patch("agent.fitness_agent.anthropic.Anthropic") as MockClient:
            from agent.fitness_agent import FitnessAgent
            instance = FitnessAgent(db_path=str(tmp_path / "test.db"))
            instance._client = MockClient.return_value
            yield instance


class TestAgentChat:
    def test_simple_text_response(self, agent):
        agent._client.messages.create.return_value = _make_text_response(
            "Hello! How can I help with your fitness goals?"
        )
        result = agent.chat("Hello")
        assert "Hello" in result or "help" in result.lower()

    def test_tool_use_lookup_nutrition(self, agent):
        # First call: agent requests lookup_nutrition tool
        # Second call: agent returns a text response using the tool result
        agent._client.messages.create.side_effect = [
            _make_tool_use_response("lookup_nutrition", "tu_001", {"food_name": "banana", "quantity_grams": 100}),
            _make_text_response("A banana (100g) has 89 calories, 1.1g protein, 23g carbs."),
        ]
        result = agent.chat("How many calories are in a banana?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tool_use_log_meal(self, agent):
        agent._client.messages.create.side_effect = [
            _make_tool_use_response("log_meal", "tu_002", {
                "food_name": "chicken breast",
                "calories": 330,
                "protein_g": 62,
                "carbs_g": 0,
                "fat_g": 7.2,
                "quantity_g": 200,
            }),
            _make_text_response("Logged 200g chicken breast: 330 kcal."),
        ]
        result = agent.chat("I ate 200g of chicken breast")
        assert isinstance(result, str)

    def test_tool_use_daily_summary(self, agent):
        agent._client.messages.create.side_effect = [
            _make_tool_use_response("get_daily_summary", "tu_003", {}),
            _make_text_response("Today you've consumed 650 calories."),
        ]
        result = agent.chat("What have I eaten today?")
        assert isinstance(result, str)

    def test_reset_clears_history(self, agent):
        agent._history = [{"role": "user", "content": "test"}]
        agent.reset()
        assert agent._history == []

    def test_conversation_history_grows(self, agent):
        agent._client.messages.create.return_value = _make_text_response("Got it!")
        agent.chat("First message")
        assert len(agent._history) == 2  # user + assistant

    def test_unknown_tool_returns_error_in_result(self, agent):
        result = agent._call_tool("nonexistent_tool", {})
        assert "error" in result


class TestToolDispatch:
    def test_dispatch_lookup_nutrition(self, agent):
        result = agent._call_tool("lookup_nutrition", {"food_name": "banana", "quantity_grams": 100})
        assert "calories" in result
        assert result["calories"] > 0

    def test_dispatch_calculate_body_metrics(self, agent):
        result = agent._call_tool("calculate_body_metrics", {
            "weight_kg": 80, "height_cm": 180, "age": 25, "gender": "male"
        })
        assert "bmr" in result
        assert result["bmr"] > 0

    def test_dispatch_log_meal(self, agent):
        result = agent._call_tool("log_meal", {
            "food_name": "oats",
            "calories": 389,
            "protein_g": 17,
            "carbs_g": 66,
            "fat_g": 7,
        })
        assert result.get("success") is True

    def test_dispatch_daily_summary(self, agent):
        result = agent._call_tool("get_daily_summary", {})
        assert "total_calories" in result

    def test_dispatch_meal_history(self, agent):
        result = agent._call_tool("get_meal_history", {"limit": 5})
        assert "entries" in result
        assert isinstance(result["entries"], list)

    def test_dispatch_save_user_profile(self, agent):
        result = agent._call_tool("save_user_profile", {
            "name": "Eren", "age": 25, "gender": "male",
            "weight_kg": 80, "height_cm": 180,
            "activity_level": "active", "goal": "gain_muscle",
        })
        assert result.get("success") is True

    def test_tool_error_returns_error_dict(self, agent):
        result = agent._call_tool("lookup_nutrition", {"food_name": "zzz_unknown_food_xyz"})
        assert "error" in result
