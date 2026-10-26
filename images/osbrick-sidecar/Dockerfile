FROM registry.ci.openshift.org/ocp/5.1:base-rhel10 AS builder

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install build-time dependencies for Python wheel compilation and
# gRPC stub generation.
RUN dnf install -y --setopt=tsflags=nodocs \
    gcc \
    python3-devel \
    python3-pip \
    && dnf clean all && rm -rf /var/cache/dnf/*

WORKDIR /build

# Build wheels for the gRPC stack (no RPM equivalent).
# os-brick and its dependencies are installed as RPMs in the
# runtime stage.
COPY images/osbrick-sidecar/requirements-grpc.txt .
RUN pip3 wheel --no-cache-dir --wheel-dir=/wheels -r requirements-grpc.txt

# Install grpcio-tools (builder only) so protoc is available for
# stub generation.
RUN pip3 install --no-cache-dir grpcio-tools==1.84.0

# Generate Python gRPC stubs from the proto file.
COPY proto/osbrick/v1/connector.proto /proto/connector.proto
RUN mkdir -p /build/gen && touch /build/gen/__init__.py && python3 -m grpc_tools.protoc \
    --proto_path=/proto \
    --python_out=/build/gen \
    --grpc_python_out=/build/gen \
    /proto/connector.proto \
    && sed -i 's/^import connector_pb2/from os_brick_grpc.gen import connector_pb2/' /build/gen/connector_pb2_grpc.py

FROM registry.ci.openshift.org/ocp/5.1:base-rhel10

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install runtime dependencies for storage operations.
# OpenShift CI supplies the OpenStack RPM repository in the base image.
RUN dnf update -y && \
    dnf install -y --setopt=tsflags=nodocs --setopt=install_weak_deps=0 \
    python3 \
    python3-pip \
    iscsi-initiator-utils \
    device-mapper-multipath \
    sg3_utils \
    sysfsutils \
    sudo \
    python3-os-brick \
    && dnf clean all && rm -rf /var/cache/dnf/*

# Install gRPC wheels from the builder stage. These have no RPM
# equivalent and must come from pip.
COPY --from=builder /wheels /tmp/wheels
COPY images/osbrick-sidecar/requirements-grpc.txt /tmp/requirements-grpc.txt
RUN pip3 install --no-cache-dir --no-index --find-links=/tmp/wheels \
    -r /tmp/requirements-grpc.txt \
    && dnf remove -y python3-pip \
    && dnf clean all \
    && rm -rf /tmp/wheels /tmp/requirements-grpc.txt /var/cache/dnf/*

WORKDIR /app

# Copy generated gRPC stubs.
COPY --from=builder /build/gen/ /app/os_brick_grpc/gen/

# Copy application source.
COPY sidecar/os_brick_grpc/ /app/os_brick_grpc/

# Entrypoint wrapper that symlinks host /run subdirectories into /run
# so os-brick tools find them, then starts the gRPC server.
COPY sidecar/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
