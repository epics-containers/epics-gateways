#!/usr/bin/env python

"""
Prints a list of cluster IPs or DNS names of IOCs running in the current namespace.
"""

import argparse

from kubernetes import client, config


def get_ioc_addrs(
    v1: client.CoreV1Api, namespace: str | None = None, dns_names: bool = False
) -> set:
    """Output a list cluster addresses of IOCs running in a namespace

    Args:
        v1: kubernetes client
        namespace: namespace to get the IOCs from
    """
    addrs = set()

    # choose the namespace to search for IOCs in
    if namespace is not None:
        ioc_namespace = namespace
    else:
        ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(ns_path) as f:
            ioc_namespace = f.read().strip()

    # get the pods in the namespace
    if dns_names:
        # if we want DNS names, we need to get the service names
        ret = v1.list_namespaced_service(ioc_namespace)
        for service in ret.items:
            if (
                service.metadata.labels is not None
                and "is_ioc" in service.metadata.labels
            ):
                # use the service name as the DNS name
                addrs.add(service.metadata.name)
    else:
        ret = v1.list_namespaced_pod(ioc_namespace)
        for pod in ret.items:
            if pod.metadata.labels is not None and "is_ioc" in pod.metadata.labels:
                addrs.add(pod.status.pod_ip)
    return addrs


def main():
    args = parse_args()

    # configure K8S and make a Core API client
    try:
        config.load_incluster_config()
        in_cluster = True
    except config.ConfigException:
        config.load_kube_config()
        in_cluster = False
    v1 = client.CoreV1Api()

    if not in_cluster and args.namespace is None:
        raise ValueError("--namespace must be specified when not running in-cluster")

    ips = get_ioc_addrs(v1, args.namespace, args.dns_names)
    ip_str = args.sep.join(ips)

    print(ip_str)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sep",
        type=str,
        default=" ",
        help="Separator for the outputed list of addresses",
    )
    parser.add_argument(
        "--namespace", type=str, default=None, help="Namespace to get the IOCs from"
    )
    parser.add_argument(
        "--dns-names",
        action="store_true",
        default=False,
        help="Use DNS names instead of IPs",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
