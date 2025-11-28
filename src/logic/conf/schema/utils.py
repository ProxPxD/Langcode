from typing import Annotated, Any

from pydantic import Field, StringConstraints

Alphanumeric = Annotated[str, StringConstraints(pattern=r'^[a-zA-Z0-9_-]+$')]
ConfType = dict[str, Any]
