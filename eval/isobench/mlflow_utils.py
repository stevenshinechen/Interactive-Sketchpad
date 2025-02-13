import logging
import subprocess
from contextlib import contextmanager
from urllib.parse import urlparse


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s: %(asctime)s] {%(process)d} %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def start_mlflow_server(
    mlflow_tracking_uri: str = "http://127.0.0.1:8081",
) -> subprocess.Popen:
    parsed_uri = urlparse(mlflow_tracking_uri)
    host = parsed_uri.hostname or "127.0.0.1"
    port = parsed_uri.port or 8081

    mlflow_server_process = subprocess.Popen(
        ["mlflow", "server", "--host", host, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    logger.info(
        f"Started MLflow server at {mlflow_tracking_uri} with PID {mlflow_server_process.pid}"
    )
    return mlflow_server_process


@contextmanager
def with_mlflow_server(mlflow_tracking_uri: str = "http://127.0.0.1:8081"):
    mlflow_server_process = start_mlflow_server(mlflow_tracking_uri)
    try:
        yield
    finally:
        mlflow_server_process.terminate()
        mlflow_server_process.wait()
        logger.info("MLFlow server terminated.")
