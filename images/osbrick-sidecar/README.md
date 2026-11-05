# OpenShift os-brick sidecar

This is a source-build candidate for validation by the PR's `ci/prow/images`
job. The current Dockerfile has not been built and tested end to end.

## Dependency policy

- Keep RHEL 10's Python 3.12, bootstrap pip, compilers, native libraries, and
  storage utilities as RPMs.
- Build all application Python packages, transitive Python dependencies, and
  isolated Python build dependencies from source archives with
  `pip wheel --no-binary=:all: --no-cache-dir`.
- Install only the locally built wheels into the runtime image, using
  `--no-index --only-binary=:all:`. These options consume the builder's output;
  they do not download upstream binary packages.
- Do not use the RHAI wheel index or the EL9 `python3-os-brick` RPM.

`requirements-runtime.txt` pins gRPC, protobuf, and os-brick to the versions in
`sidecar/requirements.txt`. `requirements-build.txt` adds the matching
`grpcio-tools` generator. Upstream sidecar requirements remain unchanged.

`constraints-build.txt` pins dnspython's uv_build backend to 0.9.21, which
declares Rust 1.89. The earlier source-build attempt selected uv_build 0.12.24
and failed because it required Rust 1.97 while the tested RHEL toolchain was
1.92. RHEL's pip 23.3 propagates `PIP_CONSTRAINT` into isolated build
environments. Recheck this mechanism when upgrading pip.

The runtime uses `/opt/venv` without system site packages, pip, compilers, or
`grpcio-tools`. Generated stubs overwrite the checked-in copies. A system-path
symlink lets sudo resolve the virtual environment's `privsep-helper`.

## CI validation

The final Dockerfile stage runs `smoke-test.py`. A failed import, unresolved
native library, failed sudo helper lookup, or failed Unix-socket gRPC health
check fails the image build. This is not a storage attach/detach test.

Source builds are slow. gRPC compilation defaults to two compiler jobs;
`GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS` is a build argument. The companion
`openshift/release` change removes the injected EL9 OpenStack repository and
requests 2 CPUs and 6 GiB of memory for this image, with an 8 GiB memory limit.
Check CI build duration and peak memory before tuning these settings.

After CI produces an image, the smoke test can also be run without rebuilding:

```sh
podman run --rm --network=none --entrypoint python3 \
  -e PYTHONPATH=/app \
  -v "$PWD/images/osbrick-sidecar/smoke-test.py:/tmp/smoke-test.py:ro,z" \
  <image-built-by-ci> /tmp/smoke-test.py
```

## Remaining packaging work

This build is source-only for Python packages, but it is not yet integrated
with Cachito or configured for a hermetic production build. Pip still accesses
PyPI, and Cargo fetches Rust source dependencies. Lock transitive packages,
build backends, and Rust dependencies; prefetch approved sources with hashes;
and validate an offline build before production packaging.

The image retains iSCSI, multipath, SCSI, sysfs, and sudo utilities. Ceph's
`rbd` command and Python `rados`/`rbd` bindings are not supplied by installing
os-brick from PyPI and are not installed here. RBD support needs separate
packaging and validation. Validate attach/detach on actual nodes and native
extensions on each supported architecture.
