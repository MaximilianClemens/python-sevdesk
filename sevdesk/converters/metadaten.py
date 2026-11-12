from typing import Optional
from pydantic import BaseModel, Field

class Metadaten(BaseModel):
    pdf: Optional[str] = None
    docId: Optional[str] = None
    class Config:
        populate_by_name = True