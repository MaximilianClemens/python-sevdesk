"""
Beispiel 2: Kontakt-Verwaltung mit High-Level API

Zeigt verschiedene Wege, Kontakte zu suchen und zu verwalten.
"""

from sevdesk import Client

# Client initialisieren
sevdesk = Client('YOUR_API_KEY_HERE')

print("=" * 60)
print("KONTAKT-VERWALTUNG BEISPIELE")
print("=" * 60)

# 1. Nach E-Mail suchen
print("\n1️⃣  Kontakt nach E-Mail suchen:")
contact = sevdesk.contactHelper.find_by_mail('max@example.com')
if contact:
    print(f"   ✅ Gefunden: {contact.name} (ID: {contact.id_})")
else:
    print("   ❌ Nicht gefunden")

# 2. Nach Custom Field suchen (z.B. RevitId)
print("\n2️⃣  Kontakt nach Custom Field suchen:")
try:
    contact = sevdesk.contactHelper.find_by_customfield(
        field='revitoid',
        value='1234567890'
    )
    if contact:
        print(f"   ✅ Gefunden: {contact.name} (ID: {contact.id_})")
    else:
        print("   ❌ Nicht gefunden")
except Exception as e:
    print(f"   ⚠️  Fehler: {e}")

# 3. Neuen Kontakt erstellen
print("\n3️⃣  Neuen Kontakt erstellen:")
try:
    contact = sevdesk.contactHelper.create(
        name='Acme GmbH',
        email='info@acme.com'
    )
    print(f"   ✅ Erstellt: {contact.name} (ID: {contact.id_})")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# 4. Kontakt per ID abrufen
print("\n4️⃣  Kontakt per ID abrufen:")
try:
    contact = sevdesk.contactHelper.get_by_id(119785368)
    if contact:
        print(f"   ✅ Gefunden: {contact.name}")
        print(f"      - Status: {contact.status}")
        print(f"      - Kundennummer: {contact.customerNumber}")
    else:
        print("   ❌ Nicht gefunden")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# 5. Mehrere Kontakte auflisten
print("\n5️⃣  Alle Kontakte auflisten:")
try:
    contacts = sevdesk.contact.getContacts()
    print(f"   📋 {len(contacts)} Kontakte gefunden")
    for i, c in enumerate(contacts[:3], 1):
        print(f"      {i}. {c.name} (ID: {c.id_})")
    if len(contacts) > 3:
        print(f"      ... und {len(contacts) - 3} weitere")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

print("\n" + "=" * 60)
