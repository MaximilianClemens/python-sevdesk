"""
Sample 03: Rechnungsstatus abrufen

- Rechnung per ID oder Nummer finden
- Status interpretieren (Offen, Bezahlt, Storniert, etc.)
- Zahlungsinformationen anzeigen
"""

import os
from dotenv import load_dotenv
from sevdesk import Client

# .env laden
load_dotenv()

api_key = os.getenv('SEVDESK_API_KEY')
if not api_key:
    raise RuntimeError("SEVDESK_API_KEY nicht in .env gefunden")

sevdesk = Client(api_key)

# Status-Codes Referenz
STATUS_CODES = {
    '50': 'Entwurf (nicht gespeichert)',
    '100': 'Draft (Entwurf)',
    '200': 'Offen (nicht bezahlt)',
    '1000': 'Bezahlt / Erledigt',
}

# Zusaetzliche Status-Informationen aus anderen Feldern:
# - paidAmount > 0 und < sumGross = Teilweise bezahlt
# - enshrined != None = Festgeschrieben
# - sendDate != None = Versendet

def get_invoice_status_details(invoice):
    """Gibt detaillierte Status-Informationen zurueck."""
    status_code = invoice.status
    status_text = STATUS_CODES.get(status_code, f'Unbekannt ({status_code})')

    details = {
        'status_code': status_code,
        'status_text': status_text,
        'is_draft': status_code == '100',
        'is_open': status_code == '200',
        'is_paid': status_code == '1000',
        'is_sent': invoice.sendDate is not None,
        'is_enshrined': invoice.enshrined is not None,
        'paid_amount': float(invoice.paidAmount or 0),
        'total_gross': float(invoice.sumGross or 0),
    }

    # Teilweise bezahlt?
    if details['paid_amount'] > 0 and details['paid_amount'] < details['total_gross']:
        details['is_partially_paid'] = True
        details['remaining'] = details['total_gross'] - details['paid_amount']
    else:
        details['is_partially_paid'] = False
        details['remaining'] = details['total_gross'] - details['paid_amount']

    return details


# --- Alle Rechnungen mit verschiedenen Status abrufen ---
print("=== Rechnungsstatus Uebersicht ===\n")

# Drafts (100)
print("--- DRAFTS (Entwuerfe) ---")
drafts = sevdesk.invoiceHelper.list(status='100', limit=5)
for inv in drafts:
    print(f"  {inv.invoiceNumber or 'Ohne Nummer'}: {inv.sumGross} EUR")

# Offene (200)
print("\n--- OFFEN (nicht bezahlt) ---")
open_invoices = sevdesk.invoiceHelper.list(status='200', limit=5)
for inv in open_invoices:
    details = get_invoice_status_details(inv)
    partial = " (teilweise bezahlt)" if details['is_partially_paid'] else ""
    print(f"  {inv.invoiceNumber}: {inv.sumGross} EUR{partial}")

# Bezahlt (1000)
print("\n--- BEZAHLT / ERLEDIGT ---")
paid_invoices = sevdesk.invoiceHelper.list(status='1000', limit=5)
for inv in paid_invoices:
    print(f"  {inv.invoiceNumber}: {inv.sumGross} EUR")

# --- Einzelne Rechnung detailliert ---
print("\n\n=== Detaillierte Status-Abfrage ===")

invoice_id = os.getenv('TEST_INVOICE_ID')
invoice_number = os.getenv('TEST_INVOICE_NUMBER')

if invoice_number:
    invoice = sevdesk.invoiceHelper.find_by_number(invoice_number)
elif invoice_id:
    invoice = sevdesk.invoiceHelper.find_by_id(int(invoice_id))
else:
    # Erste offene Rechnung nehmen
    all_invoices = sevdesk.invoice.getInvoices()
    invoice = all_invoices[0] if all_invoices else None

if invoice:
    details = get_invoice_status_details(invoice)

    print(f"\nRechnung: {invoice.invoiceNumber}")
    print(f"  Kontakt: {invoice.contact.id_ if invoice.contact else 'N/A'}")
    print(f"  Datum: {invoice.invoiceDate}")
    print(f"\nStatus:")
    print(f"  Code: {details['status_code']}")
    print(f"  Text: {details['status_text']}")
    print(f"  Draft: {'Ja' if details['is_draft'] else 'Nein'}")
    print(f"  Offen: {'Ja' if details['is_open'] else 'Nein'}")
    print(f"  Bezahlt: {'Ja' if details['is_paid'] else 'Nein'}")
    print(f"  Versendet: {'Ja' if details['is_sent'] else 'Nein'}")
    print(f"  Festgeschrieben: {'Ja' if details['is_enshrined'] else 'Nein'}")
    print(f"\nZahlung:")
    print(f"  Brutto-Summe: {details['total_gross']:.2f} EUR")
    print(f"  Bezahlt: {details['paid_amount']:.2f} EUR")
    print(f"  Offen: {details['remaining']:.2f} EUR")
    if details['is_partially_paid']:
        print(f"  -> Teilweise bezahlt!")
else:
    print("Keine Rechnung gefunden.")

print("\nSample 03 abgeschlossen!")
