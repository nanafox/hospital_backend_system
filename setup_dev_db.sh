#!/bin/bash

source .env

DB_NAME="${DB_NAME}_development"

# create a user
psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Create a new PostgreSQL database and assign it to the user
psql -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER $DB_USER;"

# grant permissions to the user
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO $DB_USER;"

# Connect to the new database and set schema permissions
psql -U postgres -d $DB_NAME -c "ALTER SCHEMA public OWNER TO ${DB_USER};"
psql -U postgres -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};"

echo "User $DB_USER and Database ${DB_NAME} created successfully for development."
