"""
Undocumented Invoice Controller

Diese erweitern die Standard-Invoice-Funktionen mit nicht-offiziell dokumentierten Features.
"""

from sevdesk.controllers.invoice_controller import InvoiceController as BaseInvoiceController


class InvoiceController(BaseInvoiceController):
    """
    Erweiterte Invoice-Controller mit zusätzlichen Funktionen.
    
    Zusätzliche Methoden:
    - createInvoice() - Direktes Erstellen von Rechnungen (nicht nur Factory)
    """
    
    def createInvoice(self, body: dict):
        """
        Erstellt eine Rechnung direkt via POST /Invoice.
        
        Dies ist nicht offiziel dokumentiert, aber funktioniert und ist
        einfacher als die Factory-Methode.
        
        Args:
            body: Dict mit Invoice-Daten:
                - contact: {id, objectName}
                - contactPerson: {id, objectName}
                - invoiceDate: YYYY-MM-DD
                - invoiceNumber: str
                - addressCountry: {id, objectName}
                - status: '100' (Draft) oder '1000' (Fertig)
                - invoiceType: 'RE' (Rechnung)
                - taxRate: float
                - taxRule: {id, objectName}
                - taxText: str
                - taxType: str
                - currency: str
                - discount: int
                
        Returns:
            Dict mit gespeicherte Rechnung
        """
        response = self.client.session.request(
            method='POST',
            url=f'{self.client.api_base}/Invoice',
            json=body,
            headers={'Authorization': self.client.api_token}
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise RuntimeError(f"Fehler beim Erstellen der Rechnung (Status {response.status_code}): {response.text}")
