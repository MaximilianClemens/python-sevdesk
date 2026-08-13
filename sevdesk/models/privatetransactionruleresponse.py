from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class PrivateTransactionRuleResponse(BaseModel):
    """A rule defining which transactions to mark as private automatically."""

    id_: Optional[str] = Field(default=None, alias="id", description="The entity id")
    objectName: Optional[str] = Field(default=None, description="The entity object name, PrivateTransactionRule")
    create: Optional[str] = Field(default=None, description="Date of entity creation")
    update: Optional[str] = Field(default=None, description="Date of last entity update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which the entity belongs.")
    paymentPurpose: Optional[str] = Field(default=None, description="The payment purpose of transactions to match")
    counterpartName: Optional[str] = Field(default=None, description="The counterpart name of transactions to match")
    class Config:
        populate_by_name = True