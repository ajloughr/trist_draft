#!/bin/bash
# Ensure we are in the project root directory regardless of where the script is called from
cd "$(dirname "$0")/.."

echo "Starting test containers (if not running)..."
docker compose -f docker-compose.test.yml up -d

echo "Stopping django to drop database safely..."
docker stop django-test
docker exec -i django-postgres-test psql -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'test_db' AND pid <> pg_backend_pid();"
docker exec -i django-postgres-test psql -U postgres -c "DROP DATABASE IF EXISTS test_db;"
docker exec -i django-postgres-test psql -U postgres -c "CREATE DATABASE test_db;"
docker start django-test

echo "Running migrations..."
docker exec -i django-test python manage.py migrate

echo "Cleaning 2026 CSV..."
docker exec -i django-test python scripts/clean_csv.py /code/draft_data/TRIST_Database_2026_v1.csv /code/draft_data/TRIST_Database_2026_v1_clean.csv

echo "Importing NFL players..."
docker exec -i django-postgres-test psql -U postgres -d test_db -c "COPY auction_table_nfl_player(player_id,full_name,team_short_name,team,bye,position,salary,final_year,drafted_by) FROM '/home/draft_data/TRIST_Database_2026_v1_clean.csv' DELIMITER ',' CSV HEADER;"

echo "Importing users and teams..."
docker exec -i django-test python manage.py shell < scripts/import_users.py

echo "Reset and initialization complete!"
