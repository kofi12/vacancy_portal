#!/bin/bash
# Generate an Alembic migration using the test environment

SERVICE_NAME="app"
COMPOSE_FILE="compose.test.yml"

# Check if the app container is running
RUNNING=$(docker compose -f $COMPOSE_FILE ps -q $SERVICE_NAME)

if [ -n "$RUNNING" ]; then
  echo "App container is running. Executing alembic revision inside the container."
  docker compose -f $COMPOSE_FILE exec $SERVICE_NAME alembic revision --autogenerate -m "$@"
else
  echo "App container is not running. Starting a new container to generate migration."
  docker compose -f $COMPOSE_FILE run --rm $SERVICE_NAME alembic revision --autogenerate -m "$@"
fi