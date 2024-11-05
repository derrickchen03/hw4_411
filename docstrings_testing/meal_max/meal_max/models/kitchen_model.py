from dataclasses import dataclass
import logging
import os
import sqlite3
from typing import Any

from meal_max.utils.sql_utils import get_db_connection
from meal_max.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Meal:
    """
    A dataclass instance that represents a meal with different attributes

    
    Attributes:
    id (int): The id number of the meal in the database
    meal (str): The name of the meal 
    cuisine (str): The type of cuisine the meal is
    price (float): The price of the meal
    difficulty (str): The difficulty to make the meal
    """

    id: int
    meal: str
    cuisine: str
    price: float
    difficulty: str

    def __post_init__(self):
        """
        Validates the attributes of the the given meal instance after initialization of @dataclass defined __init__

        Raises:
        ValueError: If price is a negative number, in other words, price is less than 0
        ValueError: If difficulty is not one of the acceptable values ['LOW, 'MEDIUM', 'HIGH']

        This method ensures:
        price (float) is a positive value
        difficulty (str) is set to one of the acceptable values ['LOW', 'MEDIUM', 'HIGH']
        """

        if self.price < 0:
            raise ValueError("Price must be a positive value.")
        if self.difficulty not in ['LOW', 'MED', 'HIGH']:
            raise ValueError("Difficulty must be 'LOW', 'MED', or 'HIGH'.")


def create_meal(meal: str, cuisine: str, price: float, difficulty: str) -> None:
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"Invalid price: {price}. Price must be a positive number.")
    if difficulty not in ['LOW', 'MED', 'HIGH']:
        raise ValueError(f"Invalid difficulty level: {difficulty}. Must be 'LOW', 'MED', or 'HIGH'.")
    
    """
    Create a meal with the specified arguments meal, cuisine, price, and difficulty

    Args:
    meal (str): The name of the meal
    cuisine (str): The type of cuisine the meal is
    price (float): The price the meal is
    difficulty (str): The difficulty to create the meal

    Returns:
    None

    Raises:
    ValueError: If price is a negative number
    ValueError: If difficulty is not one specified in the array ['LOW', 'MED', 'HIGH']

    """

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (meal, cuisine, price, difficulty)
                VALUES (?, ?, ?, ?)
            """, (meal, cuisine, price, difficulty))
            conn.commit()

            logger.info("Meal successfully added to the database: %s", meal)

    except sqlite3.IntegrityError:
        logger.error("Duplicate meal name: %s", meal)
        raise ValueError(f"Meal with name '{meal}' already exists")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def clear_meals() -> None:
    """
    Recreates the meals table, effectively deleting all meals.

    Returns:
    None

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_meal_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Meals cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing meals: %s", str(e))
        raise e

def delete_meal(meal_id: int) -> None:
    """
    Deletes a meal from the stored database given the meal_id, instance attribute id

    Arguments:
    meal_id (int): The id of the meal that will be deleted from the database

    Returns:
    None

    Raises:
    ValueError: If the meal with meal_id has already been deleted
    ValueError: If the meal with meal_id cannot be found in the DB
    sqllite3.Error: If there is a problem connecting the meal_id to the corresponding DB entry, signifying a error on the DB side through SQL
    """
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has already been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            cursor.execute("UPDATE meals SET deleted = TRUE WHERE id = ?", (meal_id,))
            conn.commit()

            logger.info("Meal with ID %s marked as deleted.", meal_id)

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_leaderboard(sort_by: str="wins") -> dict[str, Any]:
    """
    Returns a leaderboard that is sorted by the parameter sort_by any given meal has

    Arguments:
    sort_by (str): Takes a string to sort by, either has a default value of "wins" or any given custom value

    Returns:
    dict[str, Any]: A dictionary with the names of the meals, and the amount of wins

    Raises:
    ValueError: If the custom sort_by string is not found in the database
    sqllite3.Error: If there is a problem connecting the sort_by string to the corresponding DB key, signifying a error on the DB side through SQL
    """

    query = """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error("Invalid sort_by parameter: %s", sort_by)
        raise ValueError("Invalid sort_by parameter: %s" % sort_by)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            meal = {
                'id': row[0],
                'meal': row[1],
                'cuisine': row[2],
                'price': row[3],
                'difficulty': row[4],
                'battles': row[5],
                'wins': row[6],
                'win_pct': round(row[7] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(meal)

        logger.info("Leaderboard retrieved successfully")
        return leaderboard

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_meal_by_id(meal_id: int) -> Meal:
    """
    Retrieves a meal from the database given its meal id

    Arguments:
    meal_id (int): The id of the meal that will be retrieved from the database

    Returns:
    Meal (Meal): A given instance of the class Meal, with the corresponding id

    Raises:
    ValueError: If the meal with meal_id has been deleted from the database
    ValueError: If the meal with meal_id cannot be found in the database
    sqllite3.Error: If there is a problem connecting the meal_id to the corresponding DB entry, signifying a error on the DB side through SQL
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?", (meal_id,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_meal_by_name(meal_name: str) -> Meal:
    """
    Retrieves a meal from the database given its meal name

    Arguments:
    meal_name (str): The name of the meal that will be retrieved from the database

    Returns:
    Meal (Meal): A given instance of the class Meal, with the corresponding name

    Raises:
    ValueError: If the meal with meal_name has been deleted from the database
    ValueError: If the meal with meal_name cannot be found in the database
    sqllite3.Error: If there is a problem connecting the meal_name to the corresponding DB entry, signifying a error on the DB side through SQL
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?", (meal_name,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with name %s has been deleted", meal_name)
                    raise ValueError(f"Meal with name {meal_name} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with name %s not found", meal_name)
                raise ValueError(f"Meal with name {meal_name} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def update_meal_stats(meal_id: int, result: str) -> None:
    """
    Update the stats of the meal with corresponding meal_id. It can either be a win or loss.

    Arguments:
    meal_id (int): The id of the meal whose stat will be updated in the database
    result (str): The result of a battle between two meals, it can be one of two acceptable values, "win" or "loss"

    Return:
    None

    Raises:
    ValueError: If the meal with meal_id has been deleted from the database
    ValueError: If the meal with meal_id cannot be found in the database
    ValueError: If the result string is not an acceptable value, either "win" or "loss"
    sqllite3.Error: If there is a problem connecting the meal_id to the corresponding DB entry, signifying a error on the DB side through SQL
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            if result == 'win':
                cursor.execute("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?", (meal_id,))
            elif result == 'loss':
                cursor.execute("UPDATE meals SET battles = battles + 1 WHERE id = ?", (meal_id,))
            else:
                raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

            conn.commit()

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e
