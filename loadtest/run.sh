#!/bin/sh
# Run a k6 script against the API container directly (inside the compose network),
# so nginx rate limits don't get in the way of measuring the app itself.
#   ./loadtest/run.sh login-storm.js
set -e
cd "$(dirname "$0")"
docker run --rm -i --network clean-api_default -e BASE_URL="${BASE_URL:-http://api:3000}" \
  -e RATE="${RATE:-}" grafana/k6:latest run --quiet - < "$1"
