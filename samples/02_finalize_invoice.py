"""
Sample 02: Rechnung fertigstellen und PDF holen

- Bestehende Draft-Rechnung abrufen
- Status auf "fertig" setzen
- Rechnung rendern (PDF generieren)
- PDF herunterladen
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

# --- Rechnung per ID oder Nummer finden ---
# Entweder: invoice_id = 12345
# Oder: Per Rechnungsnummer suchen
invoice_number = os.getenv('TEST_INVOICE_NUMBER', '')

if invoice_number:
    invoice_response = sevdesk.invoiceHelper.find_by_number(invoice_number)
else:
    # Letzte Draft-Rechnung holen
    drafts = sevdesk.invoiceHelper.list(status='100', limit=1)
    invoice_response = drafts[0] if drafts else None

if not invoice_response:
    print("Keine Draft-Rechnung gefunden!")
    print("Fuehre zuerst 01_create_invoice.py aus.")
    exit(1)

invoice_id = int(invoice_response.id_)
print(f"Rechnung gefunden: {invoice_response.invoiceNumber} (ID: {invoice_id})")
print(f"  Aktueller Status: {invoice_response.status}")

# --- Status auf "fertig" setzen (status=200) ---
# Status-Codes:
#   100 = Draft (Entwurf)
#   200 = Offen (fertig, aber nicht versendet)
#   1000 = Versendet

# Hinweis: Um den Status zu aendern nutzen wir die API direkt
# da InvoiceExt fuer neue Rechnungen gedacht ist

# Rechnung finalisieren - erst als offen markieren
from sevdesk.models.invoice import Invoice
update_body = Invoice(status="200")
# sevdesk.invoice.updateInvoice(invoiceId=invoice_id, body=update_body)

# Alternative: Rechnung rendern setzt Status automatisch
print("\nRendere Rechnung als PDF...")
try:
    render_result = sevdesk.invoice.invoiceRender(invoiceId=invoice_id)
    print("  PDF erfolgreich generiert!")
except Exception as e:
    print(f"  Render fehlgeschlagen: {e}")

# --- PDF herunterladen ---
print("\nLade PDF herunter...")
try:
    pdf_content = sevdesk.invoice.invoiceGetPdf(invoiceId=invoice_id, download=True)

    if pdf_content:
        # PDF speichern
        filename = f"rechnung_{invoice_response.invoiceNumber}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_content)
        print(f"  PDF gespeichert als: {filename}")
        print(f"  Groesse: {len(pdf_content)} bytes")
    else:
        print("  Kein PDF-Inhalt erhalten")

except Exception as e:
    print(f"  PDF-Download fehlgeschlagen: {e}")

# --- Aktualisierten Status pruefen ---
updated_invoice = sevdesk.invoiceHelper.find_by_id(invoice_id)
if updated_invoice:
    print(f"\nAktualisierter Status: {updated_invoice.status}")
    # Status-Bedeutung:
    status_map = {
        '100': 'Draft',
        '200': 'Offen',
        '1000': 'Versendet/Bezahlt'
    }
    status_text = status_map.get(updated_invoice.status, 'Unbekannt')
    print(f"  ({status_text})")

print("\nSample 02 abgeschlossen!")
