"""
Beispiel 1: Einfache Rechnungserstellung mit High-Level API

Dies zeigt die neue, benutzerfreundliche API zum Erstellen von Rechnungen.
"""

from sevdesk import Client

# Client initialisieren
sevdesk = Client('YOUR_API_KEY_HERE')

# Schritt 1: Kontakt suchen oder erstellen
contact = sevdesk.contactHelper.find_by_mail('max@example.com')

if not contact:
    # Kontakt nicht gefunden - neuen erstellen
    contact = sevdesk.contactHelper.create(
        name='Max Mustermann',
        email='max@example.com'
    )
    print(f"✅ Neuer Kontakt erstellt (ID: {contact.id_})")
else:
    print(f"✅ Kontakt gefunden (ID: {contact.id_})")

# Schritt 2: Rechnung erstellen (noch nicht gespeichert)
invoice = sevdesk.invoiceHelper.new(
    contact=contact,
    invoiceNumber='REC-2025-001',
    invoiceDate='2025-12-16',
    header='Vielen Dank für Ihre Bestellung',
    headText='Rechnungsdetails:',
    footText='Zahlbar innerhalb von 14 Tagen',
    timeToPay=14
)

# Schritt 3: Positionen hinzufügen
invoice.addPosition(
    name='Beratungsleistung',
    quantity=2,
    price=100.00
)

invoice.addPosition(
    name='Lizenzgebühr',
    quantity=1,
    price=50.00
)

# Schritt 4: Speichern als Draft
invoice.save(status='100')
print(f"✅ Rechnung gespeichert (ID: {invoice._saved_id})")

# Schritt 5: PDF generieren (optional)
try:
    invoice.render()
    print("✅ Rechnung als PDF generiert")
except Exception as e:
    print(f"⚠️  PDF-Generierung fehlgeschlagen: {e}")

# Schritt 6: Als versendet markieren (optional)
# invoice.markAsSent()
# print("✅ Rechnung als versendet markiert")

print("\n✅ Beispiel erfolgreich abgeschlossen!")
