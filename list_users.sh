#!/bin/bash

# Define your SQLite database file
DB_FILE="instance/database.db"

# Define your SQL query
SQL_QUERY="SELECT id, username, register_date, last_login, last_calendar_pull FROM user;"

# Execute the query using sqlite3 command with desired output formatting options
sqlite3 "$DB_FILE" <<EOF
.mode column
.headers on
.separator ROW "\n"
.nullvalue NULL
$SQL_QUERY
EOF
