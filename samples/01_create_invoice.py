"""
Sample 01: Rechnung erstellen und Preise abrufen

- Rechnung als Draft erstellen
- Positionen hinzufuegen
- Rechnungsnummer automatisch von sevDesk
- Datum automatisch (heute)
- ID der neuen Rechnung ausgeben
- Rechnung anhand ID abrufen
- Netto-Preise der Positionen ausgeben
- MwSt und Netto-Summe ausgeben
"""

import os
from dotenv import load_dotenv
from sevdesk import Client

# .env laden
load_dotenv()

# Client initialisieren
api_key = os.getenv('SEVDESK_API_KEY')
if not api_key:
    raise RuntimeError("SEVDESK_API_KEY nicht in .env gefunden")

sevdesk = Client(api_key)

# --- Kontakt suchen oder erstellen ---
contact = sevdesk.contactHelper.find_by_mail('test@example.com')

if not contact:
    contact = sevdesk.contactHelper.create(
        name='Test Kunde',
        email='test@example.com'
    )
    print(f"Neuer Kontakt erstellt (ID: {contact.id_})")
else:
    print(f"Kontakt gefunden (ID: {contact.id_})")

# --- Rechnung erstellen (Draft) ---
# invoiceNumber leer = sevDesk generiert automatisch
# invoiceDate=None = heute
invoice = sevdesk.invoiceHelper.new(
    contact=contact,
    invoiceNumber="",  # automatisch von sevDesk
    invoiceDate=None,  # heute
    header='Rechnung',
    footText='Zahlbar innerhalb von 14 Tagen',
    timeToPay=14
)

# --- Positionen hinzufuegen ---
invoice.addPosition(
    name='Beratungsleistung',
    quantity=2,
    price=100.00,
    taxRate=19.0
)

invoice.addPosition(
    name='Software-Lizenz',
    quantity=1,
    price=250.00,
    taxRate=19.0
)

invoice.addPosition(
    name='Support-Paket',
    quantity=1,
    price=50.00,
    taxRate=19.0
)

# --- Speichern als Draft (status=100) ---
invoice.save(status='100')
print(f"\nRechnung erstellt!")
print(f"  ID: {invoice._saved_id}")

# --- Rechnung anhand ID abrufen ---
fetched_invoice = sevdesk.invoiceHelper.find_by_id(invoice._saved_id)

if fetched_invoice:
    print(f"  Rechnungsnummer: {fetched_invoice.invoiceNumber}")
    print(f"  Datum: {fetched_invoice.invoiceDate}")
    print(f"  Status: {fetched_invoice.status}")

# --- Positionen abrufen ---
positions = invoice.getPositions()
print(f"\nPositionen ({len(positions)} Stueck):")

for pos in positions:
    name = pos.name if hasattr(pos, 'name') else pos.get('name')
    price_net = pos.priceNet if hasattr(pos, 'priceNet') else pos.get('priceNet')
    quantity = pos.quantity if hasattr(pos, 'quantity') else pos.get('quantity')

    print(f"  - {name}: {price_net} EUR netto (Menge: {quantity})")

# --- Summen ausgeben ---
if fetched_invoice:
    print(f"\nSummen:")
    print(f"  Netto:  {fetched_invoice.sumNet} EUR")
    print(f"  MwSt:   {fetched_invoice.sumTax} EUR")
    print(f"  Brutto: {fetched_invoice.sumGross} EUR")

print("\nSample 01 abgeschlossen!")
