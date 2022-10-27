import sys

import pytest
from api import app

sys.path.append("../")


@pytest.fixture
def client(scope="function"):
    with app.test_client() as client:
        with app.app_context():
            yield client
