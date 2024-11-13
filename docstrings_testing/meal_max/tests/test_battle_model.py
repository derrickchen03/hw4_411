import pytest
from contextlib import contextmanager

from meal_max.models.kitchen_model import Meal
from meal_max.models.battle_model import BattleModel


@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.side_effect = None
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor for further expectations in tests

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture()
def mock_random_number(mocker):
    """Mock the random number for testing"""
    return mocker.patch("meal_max.models.battle_model.get_random", return_value=0.1)

@pytest.fixture()
def mock_update_meal_stats(mocker, mock_cursor):
    """Mock the update_meal_stats for testing"""
    update_meal_stats_mock = mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

    return update_meal_stats_mock

"""Fixtures providing sample meals for the tests."""
@pytest.fixture()
def sample_meal1():
    return Meal(5, "burger", "american", 5, "LOW")

@pytest.fixture()
def sample_meal2():
    return Meal(7, "pizza", "Italian", 2, "MED")


@pytest.fixture()
def sample_combatants(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

#Adding the test cases
def test_battle_raises_error_with_less_than_two_combatants(battle_model, sample_meal1):
    battle_model.prep_combatant(sample_meal1)

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle(battle_model, sample_combatants, mock_random_number, mock_update_meal_stats, mock_cursor):
    """
    Went to OH and asked Prof Golbus on Edstem about this unit test failing regarding a Meal ID 5 has been deleted
    Edstem Post #326
    """
    mock_cursor.fetchone.side_effect = [
        sample_combatants
    ]

    battle_model.combatants = sample_combatants
    assert len(battle_model.combatants) == 2

    mock_random_number.return_value = 0.1
    winner_meal = battle_model.battle()
    print(battle_model.combatants[0])
    assert winner_meal in ["burger", "pizza"]

    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == winner_meal

    if winner_meal == "burger": 
        mock_update_meal_stats.assert_any_call(1, "win")
        mock_update_meal_stats.assert_any_call(2, "loss")
    else:
        mock_update_meal_stats.assert_any_call(2, "win")
        mock_update_meal_stats.assert_any_call(1, "loss")

    mock_cursor.execute.assert_called()

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

def test_prep_combatant_raises_error_when_full(battle_model, sample_meal1, sample_meal2):
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    meal3 = Meal(id=3, meal='Meal3', price=11.0, cuisine='Mexican', difficulty='HIGH')
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(meal3)