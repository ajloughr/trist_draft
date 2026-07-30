#!/bin/bash
echo "Starting test containers..."
docker compose -f docker-compose.test.yml up -d

echo "Waiting for containers to be ready..."
sleep 10

echo "Creating test_db..."
docker exec -i django-postgres-test psql -U postgres -c "CREATE DATABASE test_db;" || true

echo "Running migrations..."
docker exec -i django-test python manage.py migrate

echo "Cleaning CSV..."
docker exec -i django-test python scripts/clean_csv.py /code/draft_data/TRIST_Database_2026_v3.csv /code/draft_data/TRIST_Database_2026_v3_clean.csv

echo "Importing database..."
docker exec -i django-postgres-test psql -U postgres -d test_db -c "COPY auction_table_nfl_player(player_id,full_name,team_short_name,team,bye,position,salary,final_year,drafted_by) FROM '/home/draft_data/TRIST_Database_2026_v3_clean.csv' DELIMITER ',' CSV HEADER;"

echo "Test setup complete!"
