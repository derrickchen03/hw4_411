from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

######################################################
#
#    Fixtures
#    Taken from test_song_model
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("mea_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """
    Test creating a new meal in the catalog
    """
    
    # Call the function to create a new meal
    create_meal(meal = "Meal Name", cuisine="Cuisine Name", price=1, difficulty="LOW")
    
    # Look at queries
    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Look at arguments
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Meal Name", "Cuisine Name", 1, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal name(should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.name")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with meal 'Meal Name' already exists."):
        create_meal(artist="Meal Name", title="Cuisine Name", price=1, difficulty="LOW" )
        
def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -1 \(must be a positive integer\)."):
        create_meal(artist="Meal Name", title="Cuisine Name", price=-1, difficulty="LOW" )

    # Attempt to create a meal with a non-integer price
    with pytest.raises(ValueError, match="Invalid price: invalid \(must be a positive integer\)."):
        create_meal(artist="Meal Name", title="Cuisine Name", price="chinese", difficulty="LOW" )
    
def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., not in list)"""

    # Attempt to create a meal with a difficulty not in the list
    with pytest.raises(ValueError, match="Invalid price: lalala \(must be either LOW, MEDIUM, or HIGH\)."):
        create_meal(artist="Meal Name", title="Cuisine Name", price=1, difficulty="lalala" )

    # Attempt to create a meal with a integer difficulty
    with pytest.raises(ValueError, match="Invalid price: invalid \(must be either LOW, MEDIUM, or HIGH\)."):
        create_meal(artist="Meal Name", title="Cuisine Name", price=1, difficulty=1 )
        
def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meal WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."
    
def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)
        
def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has already been deleted"):
        delete_meal(999)
        
def test_clear_catalog(mock_cursor, mocker):
    """Test clearing the entire meal catalog (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()
    
######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Name", 1, "LOW")

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Name", 1, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
    
def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (meal = "Meal Name", cuisine = "Cuisine Name", price = 1, difficulty = "LOW")
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Name", 1, "LOW")

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Name", 1, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
    
def test_get_meal_by_name_bad_name(mock_cursor):
    # Simulate that no meal exists for the given meal_name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with meal_name \"Meal Neme\" not found"):
        get_meal_by_name("Meal Neme")
        

def test_get_leaderboard(mock_cursor):
    """Test retrieving all meals ordered by play count."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal Name B", "Cuisine Name B", 2, "MEDIUM", 2, 2),
        (1, "Meal Name A", "Cuisine Name A", 1, "LOW", 1, 1),
        (3, "Meal Name C", "Cuisine Name C", 3, "HIGH", 3, 3)
    ]

    # Call the get_leaderboard function with empty string, defaults to sorting by "wins"
    meals = get_leaderboard()

    # Ensure the results are sorted by play count
    expected_result = [
        {"id": 3, "meal": "Meal Name C", "cuisine": "Cuisine Name B", "price": 3, "difficulty": "HIGH", "battles": 3, "wins": 3},
        {"id": 2, "meal": "Meal Name B", "cuisine": "Cuisine Name B", "price": 2, "difficulty": "MEDIUM", "battles": 2, "wins": 2},
        {"id": 1, "meal": "Meal Name A", "cuisine": "Cuisine Name B", "price": 1, "difficulty": "LOW", "battles": 1, "wins": 1}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins
        FROM meals
        WHERE deleted = FALSE
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_empty_catalog(mock_cursor, caplog):
    """Test that retrieving all meals in a leaderboard returns an empty list when the catalog is empty and logs a warning."""

    # Simulate that the catalog is empty (no meals)
    mock_cursor.fetchall.return_value = []

    # Call the get_leaderboard function
    result = get_leaderboard()

    # Ensure the result is an empty list
    assert result == [], f"Expected empty list, but got {result}"

    # Ensure that a warning was logged
    assert "The meal catalog is empty." in caplog.text, "Expected warning about empty catalog not found in logs."

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, battles, wins FROM meals WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
## Test for updating a meal with a win
def test_update_meal_stats_win(mock_cursor):
    """Test updating the win count of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID and win
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

## Test for updating a meal with a win
def test_update_meal_stats_win(mock_cursor):
    """Test updating the loss count of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID and win
    meal_id = 1
    update_meal_stats(meal_id, "loss")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
    
def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update wins for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1)

    # Ensure that no SQL query for updating play count was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))