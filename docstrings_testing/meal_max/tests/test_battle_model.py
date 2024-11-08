import pytest

from meal_max.models.kitchen_model import Meal
from meal_max.models.battle_model import BattleModel

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture()
def mock_random_number(mocker):
    """Mock the random number for testing"""
    return mocker.patch("meal_max.models.battle_model.get_random", return_value=0.1)

@pytest.fixture()
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats for testing"""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

"""Fixtures providing sample meals for the tests."""
@pytest.fixture()
def sample_meal1():
    return Meal(1, "burger", "american", 5, "LOW")

@pytest.fixture()
def sample_meal2():
    return Meal(2, "pizza", "Italian", 2, "MED")

@pytest.fixture()
def sample_combatants(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

#Adding the test cases
def test_battle(battle_model, sample_combatants, mock_random_number, mock_update_meal_stats):
    battle_model.combatants = sample_combatants
    assert len(battle_model.combatants) == 2

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

    mock_random_number.return_value = 0.1
    winner_meal = battle_model.battle()
    assert winner_meal in ["burger", "pizza"]

    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == winner_meal

    if winner_meal == "burger": 
        mock_update_meal_stats.assert_any_call(1, "win")
        mock_update_meal_stats.assert_any_call(2, "loss")
    else:
        mock_update_meal_stats.assert_any_call(2, "win")
        mock_update_meal_stats.assert_any_call(1, "loss")

def test_clear_combatants(battle_model, sample_combatants):
    battle_model.combatants = sample_combatants
    assert len(battle_model.combatants) == 2

    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0

def test_get_battle_score(battle_model, sample_meal1):
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 3
    score = battle_model.get_battle_score(sample_meal1)

    assert score == expected_score

def test_get_combatants(battle_model, sample_combatants):
    battle_model.combatants = sample_combatants
    combatants = battle_model.get_combatants()

    assert combatants == battle_model.combatants

def test_prep_combatant(battle_model, sample_meal1, sample_meal2):
    battle_model.prep_combatant(sample_meal1)
    assert battle_model.combatants == [sample_meal1]

    battle_model.prep_combatant(sample_meal2)
    assert battle_model.combatants == [sample_meal1, sample_meal2]

    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal1)