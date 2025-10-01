###### developer stage #######################################################
FROM ghcr.io/epics-containers/epics-base-developer:7.0.8ec2 AS developer

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
RUN pip install -r requirements.txt

# install debugging tools
RUN apt update && \
    apt install -y \
    net-tools tcpdump iproute2 iputils-ping vim && \
    rm -rf /var/lib/apt/lists/*

COPY settings/config /config

##### runtime stage ##########################################################
FROM ghcr.io/epics-containers/epics-base-runtime:7.0.8ec2 AS runtime

COPY --from=developer /venv /venv
COPY --from=developer /epics/ca-gateway /epics/ca-gateway
COPY --from=developer /epics/support/pcas /epics/support/PCAS

RUN apt update && \
    apt install -y \
    python3-distutils && \
    rm -rf /var/lib/apt/lists/*

COPY settings/config /config
