import asyncio
import pytest
import inspect
import time
from functools import partial
from pydantic import BaseModel
from nginx_install.utils import model_dump_yaml

def test_model_dump_yaml():
    class Sample(BaseModel):
        a: int = 3
        b: int = 2
        c: int = 1
    assert model_dump_yaml(Sample()) == 'a: 3\nb: 2\nc: 1\n'