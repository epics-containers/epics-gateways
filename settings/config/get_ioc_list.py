#!/usr/bin/env python

"""
Prints a list of cluster IPs or DNS names of IOCs running in the current namespace.
"""

import argparse
import ssl

from kubernetes import client, config
from urllib3.util.ssl_ import create_urllib3_context


def is_ioc(resource) -> bool:
    return resource.metadata.labels is not None and (
        "is_ioc" in resource.metadata.labels or "ioc" in resource.metadata.labels
    )


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
            if is_ioc(service):
                # use the service name as the DNS name
                addrs.add(service.metadata.name)
    else:
        ret = v1.list_namespaced_pod(ioc_namespace)
        for pod in ret.items:
            if is_ioc(pod):
                addrs.add(pod.status.pod_ip)
    return addrs


def core_v1_api() -> client.CoreV1Api:
    """Make a Core API client that accepts cluster CAs strict X.509 rejects.

    Python 3.13 and urllib3 2.4+ verify with ``VERIFY_X509_STRICT``, which
    rejects cluster root CAs that lack the Authority Key Identifier extension
    (kubectl accepts them). Only that flag is cleared: the certificate chain
    and host name are still verified.
    """
    api_client = client.ApiClient()
    if api_client.configuration.verify_ssl:
        context = create_urllib3_context()
        context.verify_flags &= ~ssl.VERIFY_X509_STRICT
        pool_kw = api_client.rest_client.pool_manager.connection_pool_kw
        pool_kw["ssl_context"] = context
    return client.CoreV1Api(api_client)


def main():
    args = parse_args()

    # configure K8S and make a Core API client
    try:
        config.load_incluster_config()
        in_cluster = True
    except config.ConfigException:
        config.load_kube_config()
        in_cluster = False
    v1 = core_v1_api()

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
