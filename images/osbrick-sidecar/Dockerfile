FROM registry.ci.openshift.org/ocp/5.1:base-rhel10 AS builder

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Bound gRPC compiler parallelism on CI workers.
ARG GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS=2
ENV GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS=${GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS}

# Compile native extensions and source-only Python build backends.
RUN dnf install -y --setopt=tsflags=nodocs \
    gcc \
    gcc-c++ \
    python3-devel \
    python3-pip \
    libffi-devel \
    openssl-devel \
    cargo \
    rust \
    pkgconf-pkg-config \
    && dnf clean all && rm -rf /var/cache/dnf/*

WORKDIR /build

# Build application packages, transitive dependencies, and isolated build
# dependencies from source. Disable the cache to exclude downloaded wheels.
COPY images/osbrick-sidecar/requirements-runtime.txt images/osbrick-sidecar/requirements-build.txt images/osbrick-sidecar/constraints-build.txt ./
# RHEL's pip 23.3 propagates PIP_CONSTRAINT into isolated build environments.
RUN PIP_CONSTRAINT=/build/constraints-build.txt python3 -m pip wheel \
    --no-cache-dir --no-binary=:all: --wheel-dir=/wheels -r requirements-build.txt

# Install the generation toolchain without accessing an index.
RUN python3 -m pip install --no-cache-dir --no-index --only-binary=:all: \
    --find-links=/wheels -r requirements-build.txt

COPY proto/osbrick/v1/connector.proto /proto/connector.proto
RUN mkdir -p /build/gen && touch /build/gen/__init__.py && python3 -m grpc_tools.protoc \
    --proto_path=/proto \
    --python_out=/build/gen \
    --grpc_python_out=/build/gen \
    /proto/connector.proto \
    && sed -i 's/^import connector_pb2/from os_brick_grpc.gen import connector_pb2/' /build/gen/connector_pb2_grpc.py

FROM registry.ci.openshift.org/ocp/5.1:base-rhel10

ENV PATH="/opt/venv/bin:${PATH}"

# Install the Python interpreter, native libraries, and storage utilities.
RUN dnf update -y && \
    dnf install -y --setopt=tsflags=nodocs --setopt=install_weak_deps=0 \
    python3 \
    python3-pip \
    libstdc++ \
    libffi \
    openssl-libs \
    iscsi-initiator-utils \
    device-mapper-multipath \
    sg3_utils \
    sysfsutils \
    sudo \
    && dnf clean all && rm -rf /var/cache/dnf/*

# Install runtime packages into an isolated environment from source-built wheels.
# Keep pip, compilers, and grpcio-tools out of the runtime environment.
COPY --from=builder /wheels /tmp/wheels
COPY images/osbrick-sidecar/requirements-runtime.txt /tmp/requirements-runtime.txt
RUN python3 -m venv --without-pip /opt/venv \
    && /usr/bin/python3 -m pip --python /opt/venv install \
    --no-cache-dir --no-index --only-binary=:all: --find-links=/tmp/wheels \
    -r /tmp/requirements-runtime.txt \
    && /usr/bin/python3 -m pip --python /opt/venv check \
    && /usr/bin/python3 -m pip --python /opt/venv freeze --all \
    && dnf remove -y python3-pip \
    && dnf clean all \
    && rm -rf /tmp/wheels /tmp/requirements-runtime.txt /var/cache/dnf/*

WORKDIR /app

# Copy generated stubs last so checked-in stubs cannot overwrite them.
COPY sidecar/os_brick_grpc/ /app/os_brick_grpc/
COPY --from=builder /build/gen/ /app/os_brick_grpc/gen/

# Symlink host /run subdirectories into /run before starting the server.
COPY sidecar/entrypoint.sh /app/entrypoint.sh
# oslo.privsep invokes "sudo privsep-helper". Expose the venv entry point
# in sudo's system search path without using system Python packages.
RUN chmod +x /app/entrypoint.sh \
    && ln -s /opt/venv/bin/privsep-helper /usr/bin/privsep-helper

# Fail the CI image build on missing native libraries or gRPC startup failures.
COPY images/osbrick-sidecar/smoke-test.py /tmp/smoke-test.py
RUN PYTHONPATH=/app python3 /tmp/smoke-test.py && rm /tmp/smoke-test.py

ENTRYPOINT ["/app/entrypoint.sh"]
