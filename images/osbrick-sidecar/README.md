# OpenShift os-brick sidecar

This image builds its Python packages from staged source archives. The image
build does not fetch Python or Rust sources. The `dnf` steps still need the
configured RPM repositories or prefetched RPMs.

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

`requirements-sources.txt` locks the application and gRPC generator closure.
`requirements-backends.txt` locks the isolated build requirements. Both files
pin source archives by SHA-256. The builder copies only matching archives into
pip's local search directory, including `uv_build` 0.9.21, which is compatible
with the RHEL 10 Rust 1.92 toolchain. When refreshing the locks, resolve for
CPython 3.12 and check the isolated backend closure with `pybuild-deps` and an
offline wheel build. Hash only the sdist for each pin. Keep build constraints
such as gRPC's exact Cython version and charset-normalizer's setuptools
upper bound when choosing shared backend versions.

The runtime uses `/opt/venv` without system site packages, pip, compilers, or
`grpcio-tools`. Generated stubs overwrite the checked-in copies. A system-path
symlink lets sudo resolve the virtual environment's `privsep-helper`.

## CI validation

The final Dockerfile stage runs `smoke-test.py`. A failed import, unresolved
native library, failed sudo helper lookup, or failed Unix-socket gRPC health
check fails the image build. This is not a storage attach/detach test.

Source builds are slow. gRPC compilation defaults to two compiler jobs;
`GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS` is a build argument. The companion
`openshift/release` change removes the injected EL9 OpenStack repository. A
Prow run must also stage the Python and Rust sources before the image build.

After CI produces an image, the smoke test can also be run without rebuilding:

```sh
podman run --rm --network=none --entrypoint python3 \
  -e PYTHONPATH=/app \
  -v "$PWD/images/osbrick-sidecar/smoke-test.py:/tmp/smoke-test.py:ro,z" \
  <image-built-by-ci> /tmp/smoke-test.py
```

## Stage sources before the build

Fetch the sdists in both requirements locks through the approved prefetch
pipeline. For Hermeto's `pip` input, use `images/osbrick-sidecar` as the package
path and set `requirements_files` to `["requirements-sources.txt"]` and
`requirements_build_files` to `["requirements-backends.txt"]`. Supply the
resulting flat sdist directory as `PREFETCHED_PIP` below. If this Hermeto
version also scans Python archives for Cargo dependencies, set
`pip.ignore_dependencies_crates: true` for the Python prefetch and handle
Cargo separately. Strict Cargo prefetch rejects the original `uv_build`
lockfile.

`uv_build` and its build backend, `maturin`, each need vendored crates. Extract
their Cargo workspaces from the verified sdists before Cargo prefetch. The
`uv_build` sdist ships a lockfile with entries for workspace members that it
omits. The extraction helper supplies a normalized lockfile that adds no
registry dependencies and leaves the staged sdist unchanged.

To prepare a build context manually in an environment approved for prefetch,
run from the repository root:

```sh
sidecar=$PWD/images/osbrick-sidecar
work=$(mktemp -d)
python3 "$sidecar/stage-sources.py" "$PREFETCHED_PIP" "$work/pip" \
  --rust-workspaces "$work/rust"
mkdir -p "$sidecar/staged/cargo"
cargo vendor --locked --versioned-dirs \
  --manifest-path "$work"/rust/uv-build/*/Cargo.toml \
  --sync "$work"/rust/maturin/*/Cargo.toml \
  "$sidecar/staged/cargo/vendor"
cp -a "$work/pip" "$sidecar/staged/pip"
podman build -f "$sidecar/Dockerfile" .
```

Start with an empty `staged/` directory apart from `.gitignore`. Do not commit
prefetched artifacts. A build system that mounts the bundle can set the
`OSBRICK_PIP_SOURCES` and `OSBRICK_CARGO_VENDOR` build arguments instead. The
Dockerfile configures Cargo's source replacement in `CARGO_HOME` because pip
unpacks the sdists into temporary directories outside the prefetch workspace.

Prow source delivery and downstream Konflux onboarding still need validation.
Test with public egress blocked. If the downstream build is fully hermetic,
ART must also provide the RPMs through its prefetch path.

## Storage validation

The image retains iSCSI, multipath, SCSI, sysfs, and sudo utilities. Ceph's
`rbd` command and Python `rados`/`rbd` bindings are not supplied by installing
os-brick from PyPI and are not installed here. RBD support needs separate
packaging and validation. Validate attach/detach on actual nodes and native
extensions on each supported architecture.
