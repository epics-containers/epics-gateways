
ARG BASE=7.0.9ec4

###### developer stage #######################################################
FROM ghcr.io/epics-containers/epics-base-developer:${BASE} AS developer

# provide some defaults for EPICS settings
ENV EPICS_CA_AUTO_ADDR_LIST=YES
ENV EPICS_PVA_AUTO_ADDR_LIST=YES
ENV CA_SERVER_PORT=5064
ENV PVA_SERVER_PORT=5075

# for compatibility with RHEL7 kernel
ENV EVENT_NOEPOLL=1

# get ca-gateway and pcas
RUN git clone --branch R2-1-3-0 --depth 1 -c advice.detachedHead=false \
      https://github.com/epics-extensions/ca-gateway.git /epics/src/ca-gateway
RUN git clone --branch v4.13.3 --depth 1 -c advice.detachedHead=false \
      https://github.com/epics-modules/pcas.git /epics/support/pcas

# hook up the dependencies
COPY settings/configure /configure
RUN cp /configure/RELEASE.local /epics/support/pcas/configure && \
    cp /configure/* /epics/src/ca-gateway/configure
# build pcas and ca-gateway
RUN cd /epics/support/pcas && make -j$(nproc)
RUN cd /epics/src/ca-gateway && make -j$(nproc)

COPY requirements.txt /
# uv can't install epics-core-libs yet so add pip
RUN uv pip install pip && \
    pip install -r requirements.txt

# install debugging tools
RUN apt update && \
    apt install -y \
    net-tools tcpdump iproute2 iputils-ping vim && \
    rm -rf /var/lib/apt/lists/*

COPY settings/config /config

##### runtime stage ##########################################################
FROM ghcr.io/epics-containers/epics-base-runtime:${BASE} AS runtime

# for compatibility with RHEL7 kernel
ENV EVENT_NOEPOLL=1

COPY --from=developer /venv /venv
COPY --from=developer /epics/ca-gateway /epics/ca-gateway
COPY --from=developer /epics/support/pcas /epics/support/PCAS
COPY --from=developer /python /python

COPY settings/config /config
