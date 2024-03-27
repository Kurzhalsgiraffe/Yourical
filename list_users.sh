#!/bin/bash

# Define your SQLite database file
DB_FILE="instance/database.db"

# Define your SQL query
SQL_QUERY="SELECT username FROM user;"

# Execute the query using sqlite3 command and print the result
sqlite3 "$DB_FILE" "$SQL_QUERY"
