from typing import Optional

from pydantic import BaseModel


class RationaleRequest(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    changePct: Optional[float] = None
