#!/bin/bash

# Must run bash script from parent directory
# if any of the commands in your code fails for any reason, the entire script fails
set -o errexit
# fail exit if one of your pipe command fails
set -o pipefail
# exits if any of your variables is not set
set -o nounset

# Requires positional input argument of dev or prod. Ex - bin/deploy.sh dev
mode=${1:-'dev'}

export ENVIRONMENT="${mode}"

if [[ "$mode" = "dev" ]]; then
  docker context use desktop-linux
  docker compose -f docker-compose.yml -p red-dawn up -d --build 
  echo "Project running. Visit http://localhost:8010/api/v1 to utilize API"
  # Static domain associated with ngrok account @robbxu gmail
  ngrok http --url=frankly-growing-urchin.ngrok-free.app 8010
fi
