#!/usr/bin/env python3
"""Select hash-locked sdists and optionally unpack the Rust prefetch inputs."""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import tarfile
import tomllib


LOCKFILES = ("requirements-sources.txt", "requirements-backends.txt")
LOCK_ENTRY = re.compile(r"([a-z0-9-]+)==(\S+) --hash=sha256:([0-9a-f]{64})")
RUST_PACKAGES = ("maturin", "uv-build")


def read_locks(directory):
    packages = {}
    for filename in LOCKFILES:
        for line in (directory / filename).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = LOCK_ENTRY.fullmatch(line)
            if match is None:
                raise ValueError(f"{filename}: invalid source lock entry: {line}")
            package, version, digest = match.groups()
            entry = (version, digest)
            if packages.setdefault(package, entry) != entry:
                raise ValueError(f"{package}: conflicting source locks")
    return packages


def verified_archives(source, packages):
    archives = {}
    for path in sorted(source.iterdir()):
        name = path.name.lower()
        stem = name.removesuffix(".tar.gz").removesuffix(".zip")
        if stem == name or "-" not in stem:
            continue
        distribution, version = stem.rsplit("-", 1)
        package = re.sub(r"[-_.]+", "-", distribution)
        entry = packages.get(package)
        if entry is None or version != entry[0].lower():
            continue
        _, expected = entry
        with path.open("rb") as archive:
            digest = hashlib.file_digest(archive, "sha256").hexdigest()
        if digest != expected:
            raise ValueError(f"{path}: SHA-256 mismatch")
        if package in archives:
            raise ValueError(f"{package}: multiple source archives")
        archives[package] = path
    if missing := packages.keys() - archives.keys():
        raise ValueError(f"Missing locked source archives: {', '.join(sorted(missing))}")
    return archives


def registry_dependencies(lockfile):
    return {
        (package["name"], package["version"], package["source"], package.get("checksum"))
        for package in tomllib.loads(lockfile.read_text())["package"]
        if "source" in package
    }


def unpack_rust_workspaces(archives, destination, lock_directory):
    destination.mkdir()
    for package in RUST_PACKAGES:
        archive = archives[package]
        workspace = destination / package
        workspace.mkdir()
        with tarfile.open(archive, "r:gz") as source:
            source.extractall(workspace, filter="data")
        manifests = list(workspace.glob("*/Cargo.toml"))
        if len(manifests) != 1 or not manifests[0].with_name("Cargo.lock").is_file():
            raise ValueError(f"{archive}: expected a Cargo workspace with Cargo.lock")
        manifest = manifests[0]
        if package == "uv-build":
            # The sdist omits workspace members that its original lock still lists.
            original = manifest.with_name("Cargo.lock")
            normalized = lock_directory / "cargo-locks" / f"{manifest.parent.name}.lock"
            if not registry_dependencies(normalized) <= registry_dependencies(original):
                raise ValueError(f"{normalized}: introduced unlocked Cargo dependencies")
            shutil.copyfile(normalized, original)
        print(manifest, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, help="directory of prefetched sdists")
    parser.add_argument("verified", type=Path, help="new directory for verified sdists")
    parser.add_argument("--rust-workspaces", type=Path, help="new directory for Cargo prefetch inputs")
    args = parser.parse_args()
    try:
        lock_directory = Path(__file__).resolve().parent
        packages = read_locks(lock_directory)
        archives = verified_archives(args.sources, packages)
        args.verified.mkdir()
        for path in archives.values():
            shutil.copyfile(path, args.verified / path.name)
        if args.rust_workspaces is not None:
            unpack_rust_workspaces(archives, args.rust_workspaces, lock_directory)
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
