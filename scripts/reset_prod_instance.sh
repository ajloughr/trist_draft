#!/bin/bash
# Script to reset the PRODUCTION instance database.
# Includes confirmation prompts to prevent accidental database wipes.

set -e

# Ensure we are in the project root directory regardless of where the script is called from
cd "$(dirname "$0")/.."

# Check for --force or -y flag
FORCE=false
for arg in "$@"; do
    if [ "$arg" = "--force" ] || [ "$arg" = "-y" ]; then
        FORCE=true
    fi
done

if [ "$FORCE" = false ]; then
    echo "================================================================="
    echo "  ⚠️  WARNING: PRODUCTION DATABASE RESET REQUESTED  ⚠️"
    echo "================================================================="
    echo "This action will COMPLETELY ERASE all production data, drafted"
    echo "players, bid histories, user rosters, and reset the database."
    echo ""
    read -p "Type 'RESET PROD' to confirm database wipe: " CONFIRMATION

    if [ "$CONFIRMATION" != "RESET PROD" ]; then
        echo "Reset cancelled. Database was NOT modified."
        exit 1
    fi
fi

echo ""
echo "Starting production containers (if not running)..."
docker compose up -d

echo "Stopping django container to wipe database schema safely..."
docker stop django
docker exec -i django-postgres psql -U postgres -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'postgres' AND pid <> pg_backend_pid();" || true
docker exec -i django-postgres psql -U postgres -d postgres -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
docker start django

echo "Running migrations on production instance..."
docker exec -i django python manage.py migrate

echo "Cleaning 2026 CSV data..."
docker exec -i django python scripts/clean_csv.py /code/draft_data/TRIST_Database_2026_v4.csv /code/draft_data/TRIST_Database_2026_v4_clean.csv

echo "Importing NFL players into production database..."
docker exec -i django-postgres psql -U postgres -d postgres -c "COPY auction_table_nfl_player(player_id,full_name,team_short_name,team,bye,position,salary,final_year,drafted_by) FROM '/home/draft_data/TRIST_Database_2026_v4_clean.csv' DELIMITER ',' CSV HEADER;"

echo "Importing users and teams..."
docker exec -i django python manage.py shell < scripts/import_users.py

echo ""
echo "================================================================="
echo "  ✅ PRODUCTION INSTANCE RESET COMPLETE!"
echo "================================================================="
