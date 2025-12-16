"""
InvoiceExt - Erweiterte Invoice-Klasse mit High-Level Funktionen

Diese Klasse erweitert das Standard-Invoice-Modell mit praktischen Methoden:
- addPosition() - Positionen hinzufügen
- save() - Als Draft oder fertig speichern
- getPDF() - PDF generieren
- render() - Als PDF rendern
"""

from typing import Optional, List
from sevdesk.models.invoice import Invoice as InvoiceBase


class InvoiceExt(InvoiceBase):
    """
    Erweiterte Invoice-Klasse mit High-Level Funktionen.
    
    Beispiel:
        invoice = InvoiceExt(...)
        invoice.addPosition(name='Service', quantity=1, price=100)
        invoice.save(status='DRAFT')
        pdf_url = invoice.getPDF()
    """
    
    # Store für noch nicht gespeicherte Positionen
    _pending_positions: List[dict] = []
    _client = None
    _saved_id = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending_positions = []
        self._saved_id = None
    
    def _set_client(self, client):
        """Intern: Setzt den Client-Referenz"""
        self._client = client
        return self
    
    def _set_saved_id(self, invoice_id):
        """Intern: Setzt die ID nach erfolgreicher Speicherung"""
        self._saved_id = invoice_id
        return self
    
    def addPosition(self, name: str, quantity: float, price: float, taxRate: float = 19.0, text: str = None) -> 'InvoiceExt':
        """
        Fügt eine Position zur Rechnung hinzu (vor dem Speichern).
        
        Args:
            name: Name der Position
            quantity: Menge
            price: Einzelpreis
            taxRate: Steuersatz (default: 19)
            text: Zusätzlicher Text (optional)
            
        Returns:
            self (für Method-Chaining)
        """
        position = {
            "name": name,
            "quantity": quantity,
            "price": price,
            "taxRate": taxRate,
        }
        if text:
            position["text"] = text
        
        self._pending_positions.append(position)
        return self
    
    def save(self, status: str = "100") -> 'InvoiceExt':
        """
        Speichert die Rechnung auf sevDesk.
        
        Args:
            status: Status der Rechnung
                   '100' = DRAFT (Entwurf)
                   '1000' = Fertig (default API status)
                   
        Returns:
            self mit gesetzter ID (für Method-Chaining)
        """
        if not self._client:
            raise RuntimeError("Client nicht gesetzt. Verwende InvoiceHelper.new() oder setzen Sie _set_client()")
        
        # Invoice-Daten vorbereiten
        invoice_data = {
            "contact": self.contact.model_dump(by_alias=True) if hasattr(self.contact, 'model_dump') else {"id": self.contact.id_, "objectName": "Contact"},
            "contactPerson": self.contactPerson.model_dump(by_alias=True) if hasattr(self.contactPerson, 'model_dump') else {"id": self.contactPerson.id_, "objectName": self.contactPerson.objectName},
            "invoiceDate": self.invoiceDate,
            "invoiceNumber": self.invoiceNumber,
            "addressCountry": self.addressCountry.model_dump(by_alias=True) if hasattr(self.addressCountry, 'model_dump') else {"id": self.addressCountry.id_, "objectName": "StaticCountry"},
            "status": status,
            "invoiceType": self.invoiceType,
            "taxRate": self.taxRate,
            "taxRule": self.taxRule.model_dump(by_alias=True) if hasattr(self.taxRule, 'model_dump') else {"id": self.taxRule.id_, "objectName": "TaxRule"},
            "taxText": self.taxText,
            "taxType": self.taxType,
            "currency": self.currency,
            "discount": self.discount,
        }
        
        # Optionale Felder
        if self.header:
            invoice_data["header"] = self.header
        if self.headText:
            invoice_data["headText"] = self.headText
        if self.footText:
            invoice_data["footText"] = self.footText
        if self.timeToPay:
            invoice_data["timeToPay"] = self.timeToPay
        
        # POST Request
        response = self._client.session.request(
            method='POST',
            url=f'{self._client.api_base}/Invoice',
            json=invoice_data,
            headers={'Authorization': self._client.api_token}
        )
        
        if response.status_code in [200, 201]:
            resp_data = response.json()
            if 'objects' in resp_data:
                self._saved_id = resp_data['objects'].get('id')
                
                # Positionen hinzufügen, falls vorhanden
                if self._pending_positions:
                    self._save_positions()
                
                return self
        
        raise RuntimeError(f"Fehler beim Speichern der Rechnung (Status {response.status_code}): {response.text[:200]}")
    
    def _save_positions(self):
        """
        Intern: Speichert alle pending Positionen via InvoicePos API.
        """
        from sevdesk.models.invoicepos import InvoicePos
        from sevdesk.converters.invoice import Invoice
        from sevdesk.converters.unity import Unity
        
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden")
        
        for pos_data in self._pending_positions:
            # InvoicePos-Objekt erstellen
            invoice_pos = InvoicePos(
                objectName="InvoicePos",
                invoice=Invoice(id_=self._saved_id, objectName="Invoice"),
                quantity=pos_data["quantity"],
                price=pos_data["price"],
                name=pos_data["name"],
                unity=Unity(id_=1, objectName="Unity"),  # 1 = Stück
                taxRate=pos_data.get("taxRate", 19.0),
                text=pos_data.get("text"),
                mapAll=True
            )
            
            # Position speichern
            try:
                # Direkt via POST da der Controller keine create-Methode hat
                pos_dict = invoice_pos.model_dump(by_alias=True, exclude_none=True)
                
                response = self._client.session.request(
                    method='POST',
                    url=f'{self._client.api_base}/InvoicePos',
                    json=pos_dict,
                    headers={'Authorization': self._client.api_token}
                )
                
                if response.status_code not in [200, 201]:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
                    
            except Exception as e:
                # Fehler bei Position ignorieren und weitermachen
                print(f"   ⚠️  Warnung: Position '{pos_data['name']}' konnte nicht gespeichert werden: {e}")
        
        # Pending Positionen leeren
        self._pending_positions = []
    
    def render(self) -> str:
        """
        Rendert die Rechnung als PDF.
        
        Returns:
            PDF-URL (zum Download)
        """
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")
        
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")
        
        try:
            result = self._client.invoice.invoiceRender(self._saved_id)
            return result
        except Exception as e:
            raise RuntimeError(f"Fehler beim Rendern: {e}")
    
    def getPDF(self, download: bool = False) -> Optional[bytes]:
        """
        Lädt die PDF der Rechnung herunter.
        
        Args:
            download: Ob die Datei heruntergeladen werden soll
            
        Returns:
            PDF-Inhalt (bytes) oder URL
        """
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")
        
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")
        
        try:
            result = self._client.invoice.invoiceGetPdf(self._saved_id, download=download)
            return result
        except Exception as e:
            raise RuntimeError(f"Fehler beim PDF-Download: {e}")
    
    def markAsSent(self) -> 'InvoiceExt':
        """Markiert die Rechnung als versendet."""
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")
        
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")
        
        try:
            self._client.invoice.invoiceSendBy(self._saved_id)
            return self
        except Exception as e:
            raise RuntimeError(f"Fehler beim Markieren als versendet: {e}")
    
    def getPositions(self) -> List[dict]:
        """Ruft die Positionen der gespeicherten Rechnung ab."""
        if not self._saved_id:
            return self._pending_positions
        
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")
        
        try:
            return self._client.invoice.getInvoicePositionsById(self._saved_id)
        except Exception:
            return self._pending_positions
