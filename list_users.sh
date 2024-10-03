#!/bin/bash

# Define your SQLite database file
DB_FILE="instance/database.db"

# Define your SQL queries
SQL_QUERY="
SELECT id,
       username,
       register_date,
       last_login,
       last_calendar_update,
       last_calendar_pull,
       ROUND(julianday('now') - julianday(last_calendar_pull), 2) AS days_since_last_pull
FROM user;"

COUNT_QUERY="SELECT COUNT(*) FROM user;"

# Execute the queries using sqlite3 command with desired output formatting options

# Execute the main query and print the results
sqlite3 "$DB_FILE" <<EOF
.mode column
.headers on
.separator ROW "\n"
.nullvalue NULL
$SQL_QUERY
EOF

# Count the number of users
echo "Number of users: $(sqlite3 "$DB_FILE" "$COUNT_QUERY")"
