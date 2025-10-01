#!/bin/bash

THIS_DIR="$(dirname "$(readlink -f "$0")")"
source "${THIS_DIR}/environment.sh"

ARGS=()
if [[ -n ${EPICS_CA_ADDR_LIST} ]]; then
   ARGS+=(-cip "${EPICS_CA_ADDR_LIST}")
fi

# start the CA Gateway
set -x
/epics/ca-gateway/bin/linux-x86_64/gateway -sport ${CA_SERVER_PORT} "${ARGS[@]}" \
   -pvlist /config/pvlist -access /config/access \
   -log /dev/stdout -debug ${CA_DEBUG:-0}
