#!/bin/bash
# Convenient runner script to reset test DB and execute backend, e2e, or all tests.
# Logging is enabled: output is saved to scripts/logs/ with a 10-log maximum retention.
# Usage:
#   ./scripts/run_tests.sh          # Resets DB, runs backend unit tests, resets DB, runs E2E test suites
#   ./scripts/run_tests.sh backend  # Resets DB and runs backend unit tests
#   ./scripts/run_tests.sh e2e      # Resets DB and runs end-to-end test suites
#   ./scripts/run_tests.sh <pytest args...> # Resets DB and runs custom test args

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/test_run_${TIMESTAMP}.log"

# Keep max 10 log files
cleanup_old_logs() {
    ls -t "$LOG_DIR"/test_run_*.log 2>/dev/null | tail -n +11 | xargs -r rm -f
}
cleanup_old_logs

run_tests() {
    MODE="${1:-all}"

    if [ "$MODE" = "all" ]; then
        echo "========================================="
        echo "  Resetting Test Instance Database...    "
        echo "========================================="
        bash "$SCRIPT_DIR/reset_test_instance.sh"

        echo ""
        echo "========================================="
        echo "  Running BACKEND Unit Tests...          "
        echo "========================================="
        docker exec -i django-test pytest \
            trist_draft/apps/auction_table/tests/test_admin.py \
            trist_draft/apps/auction_table/tests/test_rfa.py \
            trist_draft/apps/auction_table/tests/test_rookie.py \
            trist_draft/apps/auction_table/tests/test_roster.py \
            trist_draft/apps/auction_table/tests/test_ufa.py

        echo ""
        echo "========================================="
        echo "  Running END-TO-END Test Suites...      "
        echo "========================================="
        for f in trist_draft/apps/auction_table/tests/test_e2e_*.py; do
            echo ""
            echo "-----------------------------------------"
            echo "  Resetting DB & Running $f"
            echo "-----------------------------------------"
            bash "$SCRIPT_DIR/reset_test_instance.sh"
            docker exec -i django-test pytest "$f"
        done

    elif [ "$MODE" = "backend" ]; then
        echo "========================================="
        echo "  Resetting Test Instance Database...    "
        echo "========================================="
        bash "$SCRIPT_DIR/reset_test_instance.sh"

        echo "Running BACKEND unit tests..."
        docker exec -i django-test pytest \
            trist_draft/apps/auction_table/tests/test_admin.py \
            trist_draft/apps/auction_table/tests/test_rfa.py \
            trist_draft/apps/auction_table/tests/test_rookie.py \
            trist_draft/apps/auction_table/tests/test_roster.py \
            trist_draft/apps/auction_table/tests/test_ufa.py

    elif [ "$MODE" = "e2e" ]; then
        echo "========================================="
        echo "  Running END-TO-END Test Suites...      "
        echo "========================================="
        for f in trist_draft/apps/auction_table/tests/test_e2e_*.py; do
            echo ""
            echo "-----------------------------------------"
            echo "  Resetting DB & Running $f"
            echo "-----------------------------------------"
            bash "$SCRIPT_DIR/reset_test_instance.sh"
            docker exec -i django-test pytest "$f"
        done

    else
        echo "========================================="
        echo "  Resetting Test Instance Database...    "
        echo "========================================="
        bash "$SCRIPT_DIR/reset_test_instance.sh"

        echo "Running custom test invocation: pytest $@"
        docker exec -i django-test pytest "$@"
    fi
}

echo "Logging output to: $LOG_FILE"
run_tests "$@" 2>&1 | tee "$LOG_FILE"
