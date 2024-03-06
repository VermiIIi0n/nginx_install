import pytest
import os.path
from itertools import product
from functools import partial


@pytest.fixture(params=["core", "full"])
async def conf(request):
    yield request.param
