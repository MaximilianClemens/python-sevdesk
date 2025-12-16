"""
Beispiel 4: Batch-Operationen und Automatisierung

Zeigt, wie mehrere Rechnungen in einem Durchgang erstellt
und verwaltet werden können.
"""

from sevdesk import Client
from datetime import datetime, timedelta

# Client initialisieren
sevdesk = Client('YOUR_API_KEY_HERE')

print("=" * 60)
print("BATCH-OPERATIONEN - MEHRERE RECHNUNGEN ERSTELLEN")
print("=" * 60)

# Beispiel-Kontakte und deren Rechnungsdaten
orders = [
    {
        'email': 'acme@example.com',
        'company': 'ACME Corp',
        'invoiceNumber': 'REC-2024-001',
        'positions': [
            {'name': 'Product A', 'quantity': 2, 'price': 99.99, 'tax': 19.0},
            {'name': 'Product B', 'quantity': 1, 'price': 49.99, 'tax': 19.0},
        ]
    },
    {
        'email': 'globex@example.com',
        'company': 'Globex Corporation',
        'invoiceNumber': 'REC-2024-002',
        'positions': [
            {'name': 'Service Package', 'quantity': 1, 'price': 500.00, 'tax': 19.0},
        ]
    },
    {
        'email': 'initech@example.com',
        'company': 'Initech Inc',
        'invoiceNumber': 'REC-2024-003',
        'positions': [
            {'name': 'Consulting', 'quantity': 5, 'price': 150.00, 'tax': 19.0},
            {'name': 'Training', 'quantity': 2, 'price': 200.00, 'tax': 19.0},
        ]
    }
]

created_invoices = []
errors = []

print(f"\n📋 Verarbeite {len(orders)} Bestellungen...\n")

for order in orders:
    print(f"🔄 Verarbeite: {order['company']}")
    
    try:
        # 1. Kontakt suchen/erstellen
        contact = sevdesk.contactHelper.find_by_mail(order['email'])
        if not contact:
            print(f"   → Erstelle neuen Kontakt für {order['email']}")
            contact = sevdesk.contactHelper.create(
                name=order['company'],
                email=order['email']
            )
        
        # 2. Rechnung erstellen
        invoice = sevdesk.invoiceHelper.new(
            contact=contact,
            invoiceNumber=order['invoiceNumber'],
            invoiceDate=datetime.now().isoformat()
        )
        
        # 3. Positionen hinzufügen
        for pos in order['positions']:
            invoice.addPosition(
                name=pos['name'],
                quantity=pos['quantity'],
                price=pos['price'],
                taxRate=pos['tax']
            )
        
        # 4. Speichern als Draft
        invoice.save(status='100')
        
        created_invoices.append({
            'invoiceNumber': order['invoiceNumber'],
            'contact': contact.name,
            'id': invoice._saved_id,
            'positions': len(order['positions'])
        })
        
        print(f"   ✅ Rechnung erstellt (ID: {invoice._saved_id})")
    
    except Exception as e:
        error_msg = f"Fehler bei {order['company']}: {str(e)}"
        errors.append(error_msg)
        print(f"   ❌ {error_msg}")
    
    print()

# Zusammenfassung
print("=" * 60)
print("ZUSAMMENFASSUNG")
print("=" * 60)

print(f"\n✅ Erfolgreich erstellt: {len(created_invoices)}/{len(orders)}")
for inv in created_invoices:
    print(f"   • {inv['invoiceNumber']} - {inv['contact']} ({inv['positions']} Positionen)")

if errors:
    print(f"\n❌ Fehler: {len(errors)}")
    for error in errors:
        print(f"   • {error}")

# Optional: Alle erstellten Rechnungen auflisten
print("\n📋 Abrufen aller erstellten Rechnungen...")
try:
    all_invoices = sevdesk.invoice.getInvoices()
    recent = [inv for inv in all_invoices if inv.invoiceNumber in [o['invoiceNumber'] for o in orders]]
    print(f"   ✅ {len(recent)} Rechnungen in sevDesk gefunden")
except Exception as e:
    print(f"   ⚠️  Fehler: {e}")

print("\n" + "=" * 60)
