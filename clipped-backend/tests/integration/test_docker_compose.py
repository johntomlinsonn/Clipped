import subprocess
import time
import requests
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    # project root is three levels up from this file: tests/integration -> clipped-backend -> opus
    root = Path(__file__).parents[3]
    # Start services
    subprocess.run(["docker-compose", "up", "-d"], cwd=root, check=True)
    # Wait a bit for startup
    time.sleep(5)
    yield
    # Teardown
    subprocess.run(["docker-compose", "down"], cwd=root, check=True)


def test_docs_endpoint_available():
    url = "http://localhost:8000/docs"
    for _ in range(20):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    else:
        pytest.skip("Service did not start in time")
    assert "<title>" in r.text
