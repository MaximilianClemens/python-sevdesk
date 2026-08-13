from typing import Optional
from pydantic import BaseModel, Field


class CreatePrivateTransactionRule(BaseModel):
    objectName: str = Field(description="PrivateTransactionRule")
    paymentPurpose: Optional[str] = Field(default=None, description="The purpose of transactions that you want to match")
    counterpartName: Optional[str] = Field(default=None, description="The counterpart name of transactions that you want to match")
    class Config:
        populate_by_name = True