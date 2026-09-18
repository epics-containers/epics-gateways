---
name: gateway-chart-dev
description: How to test and release changes to the epics-gateways helm chart and container, and how to roll a new release out to a beamline services repo. Use when editing helm/, settings/config/, or the Dockerfile, or when a consumer (e.g. t11-services) needs a new gateway version.
---

# Working on the epics-gateways chart

## Two network modes decide where logic can run

- `hostNetwork: true` (default): the gateways find IOCs by broadcast
  (AUTO_ADDR_LIST). A hostNetwork pod **cannot reach the Kubernetes API**,
  so nothing that talks to the API can run in that pod.
- `hostNetwork: false`: `environment.sh` lists IOC services by DNS name
  at startup, using the `default-full-access-mounted` service account.
  Features that need the API (e.g. the `restartOnNewIocs` ioc-watcher
  sidecar) belong only in this mode. Gate them in templates with
  `and .Values.<flag> (not .Values.hostNetwork)`.

## Testing without a cluster

The repo has no tests, and helm is not installed in the sandbox. Fetch it
into `/cache` (it survives sandbox restarts):

```sh
mkdir -p /cache/bin && curl -sSfL https://get.helm.sh/helm-v3.17.4-linux-amd64.tar.gz \
  | tar xz --no-same-owner -C /cache/bin --strip-components=1 linux-amd64/helm
/cache/bin/helm lint helm
/cache/bin/helm template gw helm --set restartOnNewIocs=true,hostNetwork=false
```

- Render each combination of the relevant flags, including
  `overrideConfig=true`, which adds its own volume.
- For Python in `helm/files/` or `settings/config/`, make a uv venv with
  `kubernetes` and check the logic against `types.SimpleNamespace` fake pods.
- Delete `helm/files/__pycache__` afterwards so that it is not committed.

Scripts in `helm/files/` ship with the chart as a ConfigMap, so they need
no new image. Scripts in `settings/config/` are baked into the image, and
`overrideConfig` replaces the whole of `/config` with the user's copy.

## Releasing

- Pushing a tag such as `2026.9.3` runs CI. CI builds and pushes the image
  and publishes the chart to `oci://ghcr.io/epics-containers/epics-gateways`
  with version = the tag.
- The chart's `version`/`appVersion` in `helm/Chart.yaml` are overwritten
  at package time; do not bump them by hand.
- Consumers pin the chart in `services/<ixx>-epics-gateways/Chart.yaml`
  (dependency `epics-gateways`) and set values under the `epics-gateways:`
  key in `values.yaml`. To try a change there, follow t11-deployment's
  `test-service-change` skill.

## gh foot-gun

`gh pr edit` fails with a "Projects (classic) is being deprecated" GraphQL
error. Update a PR with REST instead:
`gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -F body=@file.md`.
