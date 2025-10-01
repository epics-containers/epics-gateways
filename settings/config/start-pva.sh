#!/bin/bash

THIS="$(dirname "$(readlink -f "$0")")"
source "${THIS}/environment.sh"

if [[  ${EPICS_PVA_AUTO_ADDR_LIST} = "YES" ]]; then
  BROADCAST=\"bcastport\":5076,
else
  BROADCAST=""
fi

if [[ ${EPICS_PVA_AUTO_ADDR_LIST} == "YES" ]]; then
  auto_addr_list=true
else
  auto_addr_list=false
fi

# fix up the templated pva gateway config
set -x
cat ${THIS}/pvagw.template |
  sed \
    -e "s/auto_addr_list/${auto_addr_list}/" \
    -e "s/PVA_SERVER_PORT/${PVA_SERVER_PORT}/" \
    -e "s/EPICS_PVA_AUTO_ADDR_LIST/${EPICS_PVA_AUTO_ADDR_LIST}/" \
    -e "s/EPICS_PVA_ADDR_LIST/${EPICS_PVA_ADDR_LIST}/" \
    -e "s/BROADCAST/${BROADCAST}/" \
    > /tmp/pvagw.config

# background the PVA Gateway
pvagw /tmp/pvagw.config
