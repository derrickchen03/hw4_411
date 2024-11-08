from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import {
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
}

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
    create_meal(meal = "Meal Name", cuisine="Cuisine Name", Price=1, difficult="LOW")
    
    # Look at queries
    expected_query = normalize_whitespace("""
        INSERT INTO songs (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Look at arguments
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Meal Name", "Cuisine Name", 1, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
