"""
Sample 04: Rechnung stornieren

- Rechnung finden
- Rechnung stornieren (cancelInvoice)
- Stornorechnung abrufen
- Details der Stornorechnung anzeigen
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

# --- Rechnung zum Stornieren finden ---
# ACHTUNG: Nur offene Rechnungen (status=200) koennen storniert werden!
# Drafts (100) koennen einfach geloescht werden.

invoice_id = os.getenv('CANCEL_INVOICE_ID')

if not invoice_id:
    # Suche eine offene Rechnung zum Testen
    print("Suche offene Rechnung zum Stornieren...")
    open_invoices = sevdesk.invoiceHelper.list(status='200', limit=1)

    if not open_invoices:
        print("Keine offene Rechnung gefunden!")
        print("Setze CANCEL_INVOICE_ID in .env oder erstelle erst eine offene Rechnung.")
        print("\nHinweis: Nur offene Rechnungen (status=200) koennen storniert werden.")
        exit(1)

    invoice = open_invoices[0]
    invoice_id = int(invoice.id_)
else:
    invoice_id = int(invoice_id)
    invoice = sevdesk.invoiceHelper.find_by_id(invoice_id)

print(f"Zu stornierende Rechnung: {invoice.invoiceNumber}")
print(f"  ID: {invoice_id}")
print(f"  Status: {invoice.status}")
print(f"  Brutto: {invoice.sumGross} EUR")

# --- Sicherheitsabfrage ---
print("\n" + "=" * 50)
print("ACHTUNG: Diese Aktion erstellt eine Stornorechnung!")
print("=" * 50)
confirm = input("Wirklich stornieren? (ja/nein): ")

if confirm.lower() != 'ja':
    print("Abgebrochen.")
    exit(0)

# --- Rechnung stornieren ---
print("\nStorniere Rechnung...")

try:
    # cancelInvoice gibt die Stornorechnung zurueck
    cancellation_invoice = sevdesk.invoice.cancelInvoice(invoiceId=invoice_id)

    print("Rechnung erfolgreich storniert!")

    # Stornorechnung-Details
    if cancellation_invoice:
        cancel_id = cancellation_invoice.id_ if hasattr(cancellation_invoice, 'id_') else None
        cancel_number = cancellation_invoice.invoiceNumber if hasattr(cancellation_invoice, 'invoiceNumber') else None

        print(f"\nStornorechnung erstellt:")
        print(f"  ID: {cancel_id}")
        print(f"  Nummer: {cancel_number}")

        # Vollstaendige Stornorechnung abrufen
        if cancel_id:
            full_cancellation = sevdesk.invoiceHelper.find_by_id(int(cancel_id))
            if full_cancellation:
                print(f"  Datum: {full_cancellation.invoiceDate}")
                print(f"  Typ: {full_cancellation.invoiceType}")
                print(f"  Brutto: {full_cancellation.sumGross} EUR")
                print(f"  Status: {full_cancellation.status}")

except Exception as e:
    print(f"Fehler beim Stornieren: {e}")
    exit(1)

# --- Original-Rechnung neu abrufen ---
print("\n--- Status der Original-Rechnung ---")
original = sevdesk.invoiceHelper.find_by_id(invoice_id)
if original:
    print(f"  Nummer: {original.invoiceNumber}")
    print(f"  Status: {original.status}")
    # Nach Stornierung sollte Status 750 (storniert) sein

# --- Alle Stornorechnungen auflisten ---
print("\n--- Stornorechnungen im System ---")
# invoiceType 'SR' = Stornorechnung
all_invoices = sevdesk.invoice.getInvoices()
cancellations = [inv for inv in all_invoices if inv.invoiceType == 'SR']

for cancel in cancellations[:5]:
    print(f"  {cancel.invoiceNumber}: {cancel.sumGross} EUR ({cancel.invoiceDate})")

print("\nSample 04 abgeschlossen!")
