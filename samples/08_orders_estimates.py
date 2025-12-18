"""
Sample 08: Angebote (Orders) verwalten

Order-Typen:
- AN = Angebot (Estimate)
- AB = Auftragsbestaetigung (Order Confirmation)
- LI = Lieferschein (Delivery Note)

- Angebot erstellen mit Positionen
- PDF generieren
- Status aendern
- Alle Angebote auflisten
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

# --- Kontakt suchen/erstellen ---
contact = sevdesk.contactHelper.find_by_mail('test@example.com')
if not contact:
    contact = sevdesk.contactHelper.create(
        name='Test Kunde',
        email='test@example.com'
    )
    print(f"Neuer Kontakt erstellt (ID: {contact.id_})")
else:
    print(f"Kontakt gefunden (ID: {contact.id_})")

# --- Angebot erstellen ---
print("\n=== Neues Angebot erstellen ===\n")

import time
order_number = f'AN-{int(time.time())}'

order = sevdesk.orderHelper.new(
    contact=contact,
    orderNumber=order_number,
    orderType='AN',  # Angebot
    header='Angebot fuer IT-Dienstleistungen',
    headText='<p>Vielen Dank fuer Ihre Anfrage. Gerne unterbreiten wir Ihnen folgendes Angebot:</p>',
    footText='<p>Dieses Angebot ist 30 Tage gueltig.</p>',
)

# Positionen hinzufuegen (Method Chaining)
order.addPosition('Beratung', quantity=10, price=150.00, taxRate=19.0)
order.addPosition('Entwicklung', quantity=20, price=120.00, taxRate=19.0)
order.addPosition('Projektmanagement', quantity=5, price=100.00, taxRate=19.0)

# Speichern
order.save()
print(f"Angebot erstellt: ID {order.id}")

# --- PDF generieren ---
print("\nGeneriere PDF...")
pdf = order.getPDF()
if pdf:
    filename = f"angebot_{order.id}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf)
    print(f"  PDF gespeichert: {filename} ({len(pdf)} bytes)")

# --- Alle Angebote auflisten ---
print("\n=== Alle Angebote ===\n")
estimates = sevdesk.orderHelper.get_estimates()
print(f"  {len(estimates)} Angebot(e) gefunden")

for o in estimates[:5]:
    gross = float(o.sumGross) if o.sumGross else 0
    status = sevdesk.orderHelper.get_status_label(o.status)
    print(f"  - {o.orderNumber}: {gross:,.2f} EUR ({status})")

# --- Nach Status filtern ---
print("\n=== Angebote nach Status ===\n")
for status_code in ['100', '200', '500']:
    orders = sevdesk.orderHelper.list(status=int(status_code))
    label = sevdesk.orderHelper.get_status_label(status_code)
    print(f"  {label}: {len(orders)}")

# --- Summen berechnen ---
print("\n=== Summen aller Angebote ===\n")
totals = sevdesk.orderHelper.calculate_totals(estimates)
print(f"  Anzahl: {totals['count']}")
print(f"  Netto:  {totals['net']:,.2f} EUR")
print(f"  MwSt:   {totals['tax']:,.2f} EUR")
print(f"  Brutto: {totals['gross']:,.2f} EUR")

# --- Positionen eines Angebots ---
if estimates:
    print(f"\n=== Positionen von {estimates[0].orderNumber} ===\n")
    positions = sevdesk.orderHelper.get_positions(int(estimates[0].id_))
    for pos in positions:
        price = float(pos.price) if pos.price else 0
        qty = float(pos.quantity) if pos.quantity else 0
        print(f"  - {pos.name}: {qty} x {price:,.2f} EUR")

print("\nSample 08 abgeschlossen!")
