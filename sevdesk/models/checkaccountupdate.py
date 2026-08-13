from typing import Optional
from pydantic import BaseModel, Field


class CheckAccountUpdate(BaseModel):
    """CheckAccount model. Responsible for the payment accounts."""

    name: Optional[str] = Field(default=None, description="Name of the check account")
    defaultAccount: Optional[int] = Field(default=None, description="Defines if this check account is the default account.")
    autoMapTransactions: Optional[int] = Field(default=None, description="Defines if transactions on this account are automatically mapped to invoice and vouchers when imported if possible.")
    accountingNumber: Optional[str] = Field(default=None, description="The booking account used for this bank account, e.g. 1800 in SKR04 and 1200 in SKR03. Must be unique among all your CheckAccounts. Ignore to use a sensible default.")
    iban: Optional[str] = Field(default=None, description="IBAN of a bank account")
    bic: Optional[str] = Field(default=None, description="BIC of the related bank")
    class Config:
        populate_by_name = True