#!/usr/bin/env python

"""
Runs as a sidecar in the gateway pod. Deletes the pod whenever an IOC service
is created in the namespace after the gateways started.

In cluster network mode the gateways find IOCs by the DNS names of the IOC
services that exist when they start, so they never search for a service
created later, e.g. when the whole namespace comes up at once. The
StatefulSet recreates the pod, restarting both gateways, which then list it.

A restarted IOC needs no gateway restart: its service keeps its cluster IP,
and the gateways' CA and PVA clients reconnect to the new pod by themselves.
Restarting the gateways would drop every client connection, e.g. in the middle
of a scan. A service that is deleted and created again gets a new cluster IP,
and its new creation time causes a restart.

The check is stateless: each poll compares the newest IOC service creation
time with the start time of the gateway containers, so restarts of this
watcher do not lose or repeat any work.
"""

import os
import time
from datetime import datetime, timezone

from kubernetes import client, config

# the gateway pod this sidecar runs in
POD_NAME = os.environ["POD_NAME"]
# the name of this sidecar's container, ignored when checking gateway start times
WATCHER_CONTAINER = "ioc-watcher"
# seconds between polls of the Kubernetes API
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "10"))
# seconds with no new IOC services before restarting, so that a batch of IOCs
# created together causes a single gateway restart
SETTLE_SECONDS = int(os.environ.get("SETTLE_SECONDS", "10"))

NS_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"


def log(msg: str):
    print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}", flush=True)


def is_ioc(resource) -> bool:
    """The same test as settings/config/get_ioc_list.py, which lists the
    services that the gateways search"""
    labels = resource.metadata.labels
    return labels is not None and ("is_ioc" in labels or "ioc" in labels)


def started_at(pod) -> datetime | None:
    """Return the time the last of a pod's gateway containers started, or None
    if they are not all running"""
    if pod.metadata.deletion_timestamp is not None:
        return None
    statuses = [
        s for s in pod.status.container_statuses or [] if s.name != WATCHER_CONTAINER
    ]
    if not statuses or any(s.state.running is None for s in statuses):
        return None
    return max(s.state.running.started_at for s in statuses)


def check(v1: client.CoreV1Api, namespace: str):
    gateway = v1.read_namespaced_pod(POD_NAME, namespace)
    gateway_started = started_at(gateway)
    if gateway_started is None:
        return

    newer = {}
    for service in v1.list_namespaced_service(namespace).items:
        if is_ioc(service) and service.metadata.deletion_timestamp is None:
            created = service.metadata.creation_timestamp
            if created > gateway_started:
                newer[service.metadata.name] = created
    if not newer:
        return

    newest = max(newer.values())
    if (datetime.now(timezone.utc) - newest).total_seconds() < SETTLE_SECONDS:
        return

    log(
        f"IOC services created since gateways started at {gateway_started.isoformat()}: "
        f"{' '.join(sorted(newer))}"
    )
    log(f"restarting gateway pod {POD_NAME}")
    v1.delete_namespaced_pod(POD_NAME, namespace)


def main():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    with open(NS_PATH) as f:
        namespace = f.read().strip()

    log(f"watching for new IOCs in {namespace} to restart gateway pod {POD_NAME}")
    while True:
        try:
            check(v1, namespace)
        except Exception as e:
            log(f"check failed: {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
