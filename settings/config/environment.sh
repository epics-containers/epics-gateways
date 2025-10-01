#!/bin/bash

THIS_DIR="$(dirname "$(readlink -f "$0")")"

if [[ ${EPICS_CA_AUTO_ADDR_LIST} == "NO" ]]; then

  # when in the cluster network we scan the namespace for IOCs and set the
  # EPICS_CA_ADDR_LIST and EPICS_PVA_ADDR_LIST environment variables to the
  # DNS names of the IOCs in the namespace.
  #
  # It would be good to do this always but we do not have permission to call
  # the Kubernetes API from a hostNetwork pod.

  if [[ -z ${EPICS_CA_ADDR_LIST} ]]; then
    echo "EPICS_CA_ADDR_LIST is not set, discovering IOCs DNS names in the namespace"
    export EPICS_CA_ADDR_LIST=$(python3 ${THIS_DIR}/get_ioc_list.py --dns-names)
  fi

  if [[ -z ${EPICS_PVA_ADDR_LIST} ]]; then
    echo "EPICS_PVA_ADDR_LIST is not set, discovering IOCs DNS names in the namespace"
    export EPICS_PVA_ADDR_LIST="$(python3 ${THIS_DIR}/get_ioc_list.py --dns-names)"
  fi

fi

echo "Using EPICS_CA_ADDR_LIST: ${EPICS_CA_ADDR_LIST}"
echo "Using EPICS_PVA_ADDR_LIST: ${EPICS_PVA_ADDR_LIST}"
