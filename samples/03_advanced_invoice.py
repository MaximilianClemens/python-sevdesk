"""
Beispiel 3: Erweiterte Rechnungsverwaltung

Zeigt fortgeschrittene Operationen mit Rechnungen:
- Mehrere Positionen hinzufügen
- PDF generieren
- Als versendet markieren
- Rechnungen auflisten und filtern
"""

from sevdesk import Client
from datetime import datetime, timedelta

# Client initialisieren
sevdesk = Client('YOUR_API_KEY_HERE')

print("=" * 60)
print("ERWEITERTE RECHNUNGSVERWALTUNG")
print("=" * 60)

# 1. Kontakt suchen/erstellen
print("\n1️⃣  Kontakt vorbereiten...")
contact = sevdesk.contactHelper.find_by_mail('kunde@example.com')
if not contact:
    print("   Kontakt nicht gefunden, erstelle neuen...")
    contact = sevdesk.contactHelper.create(
        name='Beispiel Kunde GmbH',
        email='kunde@example.com'
    )
print(f"   ✅ Kontakt ID: {contact.id_}")

# 2. Mehrposition-Rechnung erstellen
print("\n2️⃣  Rechnung mit mehreren Positionen erstellen...")
invoice = sevdesk.invoiceHelper.new(
    contact=contact,
    invoiceNumber=f'REC-{datetime.now().strftime("%Y%m%d%H%M%S")}',
    invoiceDate=datetime.now().isoformat()
)

# Positionen hinzufügen (fluent interface)
invoice \
    .addPosition(
        name='Consulting',
        quantity=10,
        price=150.00,
        taxRate=19.0,
        text='Senior Consulting Service'
    ) \
    .addPosition(
        name='Implementierung',
        quantity=20,
        price=100.00,
        taxRate=19.0,
        text='Implementierungs- und Integrationsarbeiten'
    ) \
    .addPosition(
        name='Support',
        quantity=1,
        price=500.00,
        taxRate=19.0,
        text='Technischer Support für 1 Monat'
    )

print(f"   ✅ 3 Positionen hinzugefügt")

# 3. Rechnung als Draft speichern
print("\n3️⃣  Rechnung speichern...")
try:
    invoice.save(status='100')  # 100 = Draft
    print(f"   ✅ Gespeichert als Draft (ID: {invoice._saved_id})")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# 4. PDF generieren
print("\n4️⃣  PDF generieren...")
try:
    pdf_result = invoice.render()
    if pdf_result:
        print(f"   ✅ PDF generiert")
        # PDF downloaden (optional)
        # pdf_data = invoice.getPDF(download=True)
        # print(f"   📄 PDF heruntergeladen")
except Exception as e:
    print(f"   ⚠️  PDF-Generierung fehlgeschlagen: {e}")

# 5. Nach Rechnung suchen
print("\n5️⃣  Nach Rechnung suchen...")
try:
    found_invoice = sevdesk.invoiceHelper.find_by_id(invoice._saved_id)
    if found_invoice:
        print(f"   ✅ Gefunden: {found_invoice.invoiceNumber}")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# 6. Rechnungen auflisten und filtern
print("\n6️⃣  Rechnungen des Kontakts auflisten...")
try:
    invoices = sevdesk.invoiceHelper.list(
        contact_id=contact.id_,
        status=None,  # Alle Status
        limit=5
    )
    print(f"   📋 {len(invoices)} Rechnungen gefunden")
    for i, inv in enumerate(invoices, 1):
        status_text = "Draft" if inv.status == "100" else "Abgeschlossen" if inv.status == "1000" else "Sonstig"
        print(f"      {i}. {inv.invoiceNumber} ({status_text})")
except Exception as e:
    print(f"   ⚠️  Fehler beim Auflisten: {e}")

# 7. Als versendet markieren
print("\n7️⃣  Als versendet markieren...")
try:
    invoice.markAsSent()
    print(f"   ✅ Markiert als versendet")
except Exception as e:
    print(f"   ⚠️  Fehler: {e}")

print("\n" + "=" * 60)
print("Hinweis: Ersetze 'YOUR_API_KEY_HERE' durch deinen echten API-Schlüssel")
print("=" * 60)
