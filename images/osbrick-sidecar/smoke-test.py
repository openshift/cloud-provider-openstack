"""Run inside the built sidecar image with /app on PYTHONPATH."""

import importlib.metadata
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from os_brick_grpc.gen import connector_pb2, connector_pb2_grpc
from os_brick_grpc.main import SERVICE_NAME


def main():
    assert sys.prefix == "/opt/venv", sys.prefix
    for package in ("pip", "grpc_tools"):
        assert importlib.util.find_spec(package) is None, package
    for command in ("gcc", "g++", "rustc", "cargo"):
        assert shutil.which(command) is None, command

    # sudo must resolve the venv helper even when it resets PATH.
    subprocess.run(["sudo", "-n", "privsep-helper", "--help"], check=True,
                   stdout=subprocess.DEVNULL)

    assert connector_pb2.DESCRIPTOR.services_by_name["OsBrickConnector"]
    assert connector_pb2_grpc.GRPC_GENERATED_VERSION == importlib.metadata.version(
        "grpcio"
    )

    # Check every installed native extension for missing shared libraries.
    for extension in Path(sys.prefix).rglob("*.so"):
        result = subprocess.run(
            ["ldd", str(extension)], text=True, capture_output=True, check=True
        )
        assert "not found" not in result.stdout, result.stdout
        print(f"Native libraries OK: {extension}")

    with tempfile.TemporaryDirectory() as directory:
        socket = f"{directory}/osbrick.sock"
        environment = dict(
            os.environ, OSBRICK_SOCKET_PATH=socket, HOST_RUN_DIR=directory
        )
        with tempfile.TemporaryFile(mode="w+") as log:
            server = subprocess.Popen(
                ["/app/entrypoint.sh"], env=environment, stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                with grpc.insecure_channel(f"unix://{socket}") as channel:
                    grpc.channel_ready_future(channel).result(timeout=30)
                    health = health_pb2_grpc.HealthStub(channel)
                    for service in ("", SERVICE_NAME):
                        response = health.Check(
                            health_pb2.HealthCheckRequest(service=service),
                            timeout=5,
                        )
                        assert response.status == health_pb2.HealthCheckResponse.SERVING
            finally:
                server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                    raise
                finally:
                    log.seek(0)
                    print(log.read())
            assert server.returncode == 0, server.returncode

    print("Runtime isolation, native libraries, generated stubs, and gRPC health OK")


if __name__ == "__main__":
    main()
