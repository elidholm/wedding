#!/usr/bin/env bash

host_port=5000
url=http://localhost:${host_port}
MAX_ATTEMPTS=30
RETRY_DELAY=1
DEV_MODE=false
STOP=false

print_usage() {
  cat <<EOF

Usage: ${0##*/} [-p <host_port>] [-d] [-s]
  -p <host_port> : Specify the host port for the application (default: 5000)
  -d             : Start containers in development mode (with watch)
  -s             : Stop and remove containers, then exit
  -h             : Display this help message
EOF
}

print_help() {
  echo 'This script is used to build and run the application in a Docker container.'
  print_usage
  exit 0
}

die() {
  echo >&2 "Error: $*"
  print_usage
  exit 1
}

parse_args() {
  OPTSTRING=:p:dsh
  while getopts $OPTSTRING opt; do
    case $opt in
    p)
      host_port=$OPTARG
      url=http://localhost:${host_port}
      ;;
    d)
      DEV_MODE=true
      ;;
    s)
      STOP=true
      ;;
    h)
      print_help
      ;;
    :)
      die "Option -$OPTARG requires an argument"
      ;;
    ?)
      die "Invalid option: -$OPTARG"
      ;;
    esac
  done
  shift $((OPTIND - 1))
}

wait_for_app() {
  local url=$1
  local attempt
  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    if curl --silent --fail --output /dev/null "$url"; then
      return 0
    fi
    sleep "$RETRY_DELAY"
  done
  return 1
}

main() {
  if [[ ! -f docker-compose.yml ]]; then
    die 'docker-compose.yml not found, run this script from the repo root'
  fi

  parse_args "$@"

  echo 'Tearing down any existing containers...'
  if ! host_port=$host_port docker compose down --remove-orphans; then
    echo 'Warning: docker compose down failed, continuing anyway' >&2
  fi

  if [[ $STOP == true ]]; then
    echo 'Stopped containers, exiting'
    exit 0
  fi

  if [[ $DEV_MODE == true ]]; then
    echo 'Starting containers in development mode...'
    if ! host_port=$host_port docker compose up --build --watch; then
      die 'Failed to start containers in development mode'
    fi
  else
    echo 'Building and starting fresh containers...'
    if ! host_port=$host_port docker compose up --build -d; then
      die 'Failed to start containers'
    fi

    echo 'Waiting for the app to respond...'
    if ! wait_for_app "$url/health"; then
      die "The app did not respond @ ${url}/health after ${MAX_ATTEMPTS} attempts"
    fi

    echo "The application is up and running @ ${url}"
  fi
}

main "$@"
