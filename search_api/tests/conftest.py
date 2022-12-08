import sys
from typing import List, TypedDict

import pytest
from api import app

sys.path.append("../")


@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client
