#!/usr/bin/env bash

host_port=5000
url="http://localhost:${host_port}/"
MAX_ATTEMPTS=30
RETRY_DELAY=1

main() {
  if [[ ! -f docker-compose.yml ]]; then
    echo 'error: docker-compose.yml not found, run this script from the repo root' >&2
    exit 1
  fi

  echo 'Tearing down any existing containers...'
  if ! host_port=$host_port docker compose down --remove-orphans; then
    echo 'warning: docker compose down failed, continuing anyway' >&2
  fi

  echo 'Building and starting fresh containers...'
  if ! host_port=$host_port docker compose up --build -d; then
    echo 'error: failed to start containers' >&2
    exit 1
  fi

  echo "Waiting for the app to respond @ ${url}..."
  if ! wait_for_app; then
    echo "error: app did not respond @ ${url} after ${MAX_ATTEMPTS} attempts" >&2
    echo 'Check the logs with: docker compose logs' >&2
    exit 1
  fi

  echo
  echo "The application is up and running @ ${url}"
}

wait_for_app() {
  local attempt
  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    if curl --silent --fail --output /dev/null "$url"; then
      return 0
    fi
    sleep "$RETRY_DELAY"
  done
  return 1
}

main "$@"
