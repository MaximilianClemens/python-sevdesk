from sevdesk.base.basecontroller import BaseController


def _objects(response):
    # "from" ist ein Python-Schlüsselwort, daher eur/bwa ohne Decorator
    return response.get('objects', response) if isinstance(response, dict) else response


class AccountingReportsController(BaseController):
    """Auswertungen der Weboberfläche (undocumented API), Antworten als dict.

    Fehlende oder nicht zuordenbare Buchungen stehen jeweils unter "failures".
    """

    def getEur(self, from_date: str, until_date: str) -> dict:
        """Einnahmenüberschussrechnung, Datum als YYYY-MM-DD"""
        return _objects(self.client.request('get', '/AccountingReports/eur', {'from': from_date, 'until': until_date}))

    @BaseController.get("/AccountingReports/ustva")
    def getUstva(self, startMonth: str, endMonth: str, taxationType: str = 'IST') -> dict:
        """UStVA-Vorschau, Monate als YYYY-MM, taxationType IST oder SOLL"""
        return (yield)

    def getBwa(self, from_month: str, until_month: str,
               accountingProfitAssessmentType: str = 'REVENUE_SURPLUS_ACCOUNTING') -> dict:
        """BWA, Monate als YYYY-MM"""
        return _objects(self.client.request('get', '/AccountingReports/bwa', {
            'from': from_month, 'until': until_month,
            'accountingProfitAssessmentType': accountingProfitAssessmentType,
            'filterByCostCentre': 'false',
        }))

    @BaseController.get("/AccountingReports/balanceList")
    def getBalanceList(self, startDate: str, endDate: str) -> dict:
        """Summen- und Saldenliste, Monate als YYYY-MM"""
        return (yield)

    @BaseController.get("/AccountingReports/findTaxReceiptFor")
    def findTaxReceiptFor(self, vatReportId: int) -> dict:
        """Steuerbeleg zu einer übermittelten UStVA"""
        return (yield)

    @BaseController.get("/AccountingReports/hasBookings/")
    def hasBookings(self) -> dict:
        return (yield)

    @BaseController.get("/AccountingReports/isAnnualUstvaAvailable")
    def isAnnualUstvaAvailable(self) -> dict:
        return (yield)
