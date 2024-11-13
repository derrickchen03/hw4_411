#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing the catalog..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal, $cuisine, $price, $difficulty) to the database..."
  
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully with ID ($meal_id)."
  else
    echo "Failed to delete meal with ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal=$1

  echo "Getting meal by name '$meal'..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by '$meal'):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}

###############################################
#
# Battle
#
###############################################


start_battle() {
  echo "Starting a battle..."
  response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/battle")
  http_status=${response: -3}
  response_body=${response::-3}

  if [ "$http_status" -eq 200 ]; then
    echo "Battle completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Result JSON:"
      echo "$response_body" | jq .
    fi
  else
    echo "Failed to start battle. HTTP Status: $http_status"
    echo "Response: $response_body"
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

get_combatants() {
  echo "Retrieving current combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}

prep_combatant() {
  meal_name=$1

  echo "Preparing combatant with Meal Name ($meal_name)..."
  response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/prep-combatant" \
    -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal_name\"}")
  http_status=${response: -3}
  response_body=${response::-3}

  if [ "$http_status" -eq 200 ]; then
    echo "Combatant prepared successfully."
  else
    echo "Failed to prepare combatant. HTTP Status: $http_status"
    echo "Response: $response_body"
    exit 1
  fi
}

###############################################
#
# Leaderboard
#
###############################################

get_leaderboard() {
  echo "Getting leaderboard of meals..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}
###############################################
#
# Calling Functions
#
###############################################

check_health
check_db

create_meal "Pasta" "Italian" 12.50 "MED"
create_meal "Sushi" "Japanese" 15.99 "HIGH"
create_meal "Burger" "American" 10.00 "LOW"
create_meal "Tacos" "Mexican" 8.75 "LOW"
create_meal "Curry" "Indian" 14.20 "MED"

delete_meal_by_id 1
delete_meal_by_id 2

get_meal_by_id 3
get_meal_by_name "Tacos"

clear_meals

create_meal "Pasta" "Italian" 12.50 "MED"
create_meal "Curry" "Indian" 14.20 "MED"
create_meal "Sushi" "Japanese" 15.99 "HIGH"
create_meal "Burger" "American" 10.00 "LOW"
create_meal "Tacos" "Mexican" 8.75 "LOW"
get_meal_by_id 1

prep_combatant "Pasta"
prep_combatant "Curry"
get_combatants
start_battle
clear_combatants

get_leaderboard

