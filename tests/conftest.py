import tempfile
from typing import Iterator

import pytest


@pytest.fixture
def temp_file() -> Iterator[str]:
    with tempfile.NamedTemporaryFile("wb") as file:
        yield file.name
