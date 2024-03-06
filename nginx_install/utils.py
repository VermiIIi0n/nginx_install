import yaml
from pydantic import BaseModel


def model_dump_yaml(m: BaseModel) -> str:
    return yaml.dump(
        m.model_dump(mode="json"),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
