"""
InvoiceHelper - High-Level Rechnungs-Verwaltung

Beispiele:
    invoice = sevdesk.invoiceHelper.new(
        contact=contact,
        invoiceDate='2025-12-16',
        invoiceNumber='REC-001'
    )
    invoice.addPosition('Service', 1, 100)
    invoice.save(status='DRAFT')
    
    invoice = sevdesk.invoiceHelper.find_by_id(12345)
"""

from datetime import datetime
from typing import Optional
from sevdesk.helpermodels.invoice_ext import InvoiceExt
from sevdesk.converters.contact import Contact
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.taxrule import TaxRule


class InvoiceHelper:
    """Helper-Klasse für Rechnungs-Operationen auf hohem Level"""
    
    def __init__(self, client):
        self.client = client
    
    def new(self,
            contact,
            invoiceDate: Optional[str] = None,
            invoiceNumber: str = "",
            addressCountry_id: int = 1,
            addressCountry_name: str = "StaticCountry",
            status: str = "100",
            invoiceType: str = "RE",
            taxRate: float = 19.0,
            taxRule_id: str = "1",
            taxText: str = "Umsatzsteuer",
            taxType: str = "default",
            currency: str = "EUR",
            discount: int = 0,
            contactPerson_id: int = 1370583,
            contactPerson_name: str = "SevUser",
            header: Optional[str] = None,
            headText: Optional[str] = None,
            footText: Optional[str] = None,
            timeToPay: Optional[int] = None) -> InvoiceExt:
        """
        Erstellt eine neue Rechnung (noch nicht gespeichert).
        
        Args:
            contact: Contact-Objekt oder Contact-ID
            invoiceDate: Rechnungsdatum (default: heute)
            invoiceNumber: Rechnungsnummer
            addressCountry_id: Land-ID (1=Deutschland)
            status: Status ('100'=Draft, '1000'=Fertig)
            invoiceType: Typ ('RE'=Rechnung)
            taxRate: Steuersatz (default: 19)
            taxRule_id: Steuerregel-ID
            currency: Währung (default: EUR)
            contactPerson_id: Ansprechpartner-ID
            header: Header-Text
            headText: Kopftext
            footText: Fußtext
            timeToPay: Zahlungsfrist in Tagen
            
        Returns:
            InvoiceExt-Objekt (noch nicht gespeichert)
        """
        # Contact normalisieren
        if isinstance(contact, int):
            contact = Contact(id_=contact, objectName="Contact")
        elif isinstance(contact, dict):
            contact = Contact(id_=contact['id_'], objectName="Contact")
        elif hasattr(contact, 'id_'):
            # ContactResponse oder ähnliches Objekt -> zu Contact converter konvertieren
            contact = Contact(id_=contact.id_, objectName="Contact")
        # Sonst: Annahme dass es ein Contact-Objekt ist
        
        # Datum default auf heute
        if invoiceDate is None:
            invoiceDate = datetime.now().strftime("%Y-%m-%d")
        
        # InvoiceExt erstellen
        invoice = InvoiceExt(
            contact=contact,
            contactPerson=ContactPerson(id_=contactPerson_id, objectName=contactPerson_name),
            invoiceDate=invoiceDate,
            invoiceNumber=invoiceNumber,
            addressCountry=AddressCountry(id_=addressCountry_id, objectName=addressCountry_name),
            status=status,
            invoiceType=invoiceType,
            taxRate=taxRate,
            taxRule=TaxRule(id_=taxRule_id, objectName="TaxRule"),
            taxText=taxText,
            taxType=taxType,
            currency=currency,
            discount=discount,
            header=header,
            headText=headText,
            footText=footText,
            timeToPay=timeToPay,
            mapAll=True
        )
        
        # Client setzen für spätere Operationen
        invoice._set_client(self.client)
        
        return invoice
    
    def find_by_id(self, invoice_id: int):
        """
        Ruft eine Rechnung per ID ab.
        
        Args:
            invoice_id: ID der Rechnung
            
        Returns:
            InvoiceResponse oder None
        """
        try:
            result = self.client.invoice.getInvoiceById(invoice_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None
    
    def find_by_number(self, invoice_number: str):
        """
        Sucht eine Rechnung per Rechnungsnummer.
        
        Args:
            invoice_number: Rechnungsnummer
            
        Returns:
            InvoiceResponse oder None
        """
        try:
            invoices = self.client.invoice.getInvoices(invoiceNumber=invoice_number)
            if invoices and len(invoices) > 0:
                return invoices[0]
            return None
        except Exception:
            return None
    
    def list(self, contact_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100):
        """
        Listet Rechnungen auf.
        
        Args:
            contact_id: Optional: nur für einen Kontakt
            status: Optional: filtere nach Status
            limit: Max. Anzahl (wird durch API begrenzt)
            
        Returns:
            Liste von InvoiceResponse-Objekten
        """
        try:
            invoices = self.client.invoice.getInvoices(
                contact_id=contact_id,
                status=float(status) if status else None
            )
            return invoices[:limit] if invoices else []
        except Exception:
            return []
