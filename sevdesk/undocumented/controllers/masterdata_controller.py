from sevdesk.base.basecontroller import BaseController
from typing import Optional


class MasterDataController(BaseController):
    """Stammdaten der Weboberfläche (undocumented), Antworten als dict bzw. list[dict]"""

    @BaseController.get("/AccountDatev/Factory/getAccounts")
    def getAccounts(self, showDeactivated: Optional[bool] = None, withHidden: Optional[bool] = None) -> list[dict]:
        """Vollständige Kontenliste (GET /AccountDatev liefert nur 100)"""
        return (yield)

    @BaseController.get("/Account/Factory/selectableAccounts")
    def getSelectableAccounts(self) -> list[dict]:
        """Buchbare Konten mit erlaubten Steuerregeln und Belegarten"""
        return (yield)

    @BaseController.get("/AccountCategory/Factory/getAccountCategories")
    def getAccountCategories(self) -> list[dict]:
        return (yield)

    @BaseController.get("/TaxRuleDocumentRelation/Factory/getAllTaxRuleDocumentRelations")
    def getTaxRuleDocumentRelations(self, embed: Optional[str] = None) -> list[dict]:
        """Erlaubte Steuerregeln und -sätze je Belegart"""
        return (yield)

    @BaseController.get("/Category")
    def getCategories(self, objectType: Optional[str] = None, limit: Optional[int] = None,
                      offset: Optional[int] = None) -> list[dict]:
        return (yield)

    @BaseController.get("/CostCentre")
    def getCostCentres(self, limit: Optional[int] = None) -> list[dict]:
        return (yield)

    @BaseController.get("/PaymentMethod")
    def getPaymentMethods(self) -> list[dict]:
        return (yield)

    @BaseController.get("/TextTemplate")
    def getTextTemplates(self, objectType: Optional[str] = None, textType: Optional[str] = None,
                         limit: Optional[int] = None, offset: Optional[int] = None) -> list[dict]:
        return (yield)

    @BaseController.get("/StaticCountry")
    def getCountries(self, limit: Optional[int] = None) -> list[dict]:
        return (yield)

    @BaseController.get("/SevSequence")
    def getSequences(self, limit: Optional[int] = None) -> list[dict]:
        """Nummernkreise (Rechnungen, Belege, ...)"""
        return (yield)

    @BaseController.get("/SevSequence/Factory/getByType")
    def getSequenceByType(self, objectType: str, type: str) -> dict:
        return (yield)

    @BaseController.get("/VatReport")
    def getVatReports(self, reportingYear: Optional[int] = None, reportingPeriodCode: Optional[str] = None,
                      limit: Optional[int] = None) -> list[dict]:
        """Übermittelte UStVA mit Kennzahlen (reportingValues) und Protokoll (document)"""
        return (yield)
