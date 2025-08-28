# EPICS Gateways Container

# Intro

A container for the epics PVA gateway and epics CA gateway. Intended for running in a K8S cluster.

Includes K8S script to determine the cluster IPs or DNS names of all IOCs in the namespace. This configures the gateways to connect to all IOCs in the namespace.

# Deployment (using epics-containers)

Simply create a folder ixx-services/services/ixx-gateway and create a Chart.yaml and values.yaml file.

Chart.yaml should look like this:
```yaml
apiVersion: v2
name: ec-gateways
version: 1.0.0

type: application

dependencies:
  - name: epics-gateways
    version: 2025.7.2
    repository: "oci://ghcr.io/epics-containers"
```

values.yaml should look like this:
```yaml
epics-gateways:
  # leave blank unless you want to pin to a specific node
  nodeName:
  # set to false to run the gateway in clusterIP mode
  hostNetwork: true
```

Push your changes to a branch (and tag it if you want) and then run the following command to deploy the gateways:

```bash
module load ec/ixx
ec deploy ixx-gateway <your-branch-name>
```


# hostNetwork
When run with hostNetwork=true, the gateways use AUTO_ADDR_LIST broadcasts on the local network to discover IOCs.

When run with hostNetwork=false, the gateways use the cluster DNS names of the IOCs that were running when the gateways pod started - you are required to restart the pod if new IOCs are deployed.

# Configuration

The supplied helm chart can deploy the gateways into a K8S cluster.

At DLS the only configuration required in values.yaml is `hostNetwork: false` if you want to use the cluster DNS names of the IOCs.

You can also use `nodeName: <your-node-name>` to pin the gateway pod to a specific node. This is required for the p4x beamlines which need their gateway in the controls-dev-network. NOTE: do not run the gateway on the same node as an IOC, it will get many duplicate PC warnings.

## Overview
This diagram is an overview of the two modes of operation:

![gateway modes](gateway-modes.png)


## Customising the gateway configuration

All the startup scripts and configuration files can be overriden as follows:

- Copy `helm/config` from this repo to `ixx-services/services/ixx-gateway/config`
- Copy `gateways/settings/configmap.yaml` from this repo to `ixx-services/services/ixx-gateway/templates/configmap.yaml` (creating the templates directory)
- push the changes to your tracked branch
- delete the gateway pod in argoCD so it restarts with the new configuration
- add this field to your values.yaml
  - overrideConfig: true
- now you can edit the files in `ixx-services/services/ixx-gateway/config` to suit your needs and push the changes to your tracked branch.
