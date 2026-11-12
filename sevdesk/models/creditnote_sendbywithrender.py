from typing import Optional, Any
from pydantic import BaseModel, Field


class CreditNote_sendByWithRender(BaseModel):
    pdf: Optional[str] = Field(default=None, description="Base64-encoded PDF")
    docId: Optional[str] = None
    parameters: Optional[Any] = None
    class Config:
        populate_by_name = True