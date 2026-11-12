from sevdesk.base.basecontroller import BaseController


class DatevExportController(BaseController):
    """DATEV-Export wie in der Weboberfläche (undocumented).

    Die Spec nennt GET mit Query-Parametern, die API verlangt aber POST mit
    form-urlencoded Body. Danach wie dokumentiert: client.export.generateDownloadHash,
    getProgress und jobDownloadInfo.
    """

    @BaseController.post("/Export/createDatevCsvZipExportJob")
    def createDatevCsvZipExportJob(self, form: dict) -> dict:
        """form: startDate, endDate (Unix-Timestamps), scope (z.B. EXTC), includeDocumentImages,
        includeEnshrined, enshrineDocuments, exportByPaydate, deltaExport ('true'/'false')"""
        return (yield)

    @BaseController.post("/Export/createDatevXmlZipExportJob")
    def createDatevXmlZipExportJob(self, form: dict) -> dict:
        """form: startDate, endDate, scope, includeDocumentXml, includeEnshrined, includeExportedDocuments"""
        return (yield)

    @BaseController.get("/SevClient/{sevClientId}/getExportConfig")
    def getExportConfig(self, sevClientId: int) -> dict:
        """accountingYearBegin, Berater-/Mandantennummer und zuletzt ausgelöster Export"""
        return (yield)
