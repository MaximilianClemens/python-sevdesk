"""
Sample 09: Artikel/Produkte (Parts) verwalten

- Artikel erstellen
- Nach Nummer/Name suchen
- Preis aktualisieren
- Lagerbestand pruefen
- Alle Artikel auflisten
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

# --- Artikel suchen oder erstellen ---
print("=== Artikel suchen/erstellen ===\n")

# Artikel nach Nummer suchen
part = sevdesk.partHelper.find_by_number('CONS-01')

if part:
    print(f"Artikel gefunden: {part.name} (ID: {part.id_})")
else:
    # Neuen Artikel erstellen
    part = sevdesk.partHelper.create(
        name='Beratungsstunde',
        partNumber='CONS-01',
        price=150.00,
        taxRate=19.0,
        unity='stunde',
        text='Eine Stunde professionelle Beratung'
    )
    if part:
        print(f"Artikel erstellt: {part.name} (ID: {part.id_})")
    else:
        print("Fehler beim Erstellen des Artikels")

# --- Weitere Artikel erstellen ---
print("\n=== Weitere Artikel erstellen ===\n")

articles = [
    {'name': 'Entwicklung (Stunde)', 'partNumber': 'DEV-01', 'price': 120.00, 'unity': 'stunde'},
    {'name': 'Support (Stunde)', 'partNumber': 'SUP-01', 'price': 80.00, 'unity': 'stunde'},
    {'name': 'Webhosting (Monat)', 'partNumber': 'HOST-01', 'price': 29.90, 'unity': 'monat'},
]

for art in articles:
    existing = sevdesk.partHelper.find_by_number(art['partNumber'])
    if existing:
        print(f"  Existiert bereits: {art['partNumber']}")
    else:
        new_part = sevdesk.partHelper.create(
            name=art['name'],
            partNumber=art['partNumber'],
            price=art['price'],
            unity=art['unity'],
            taxRate=19.0
        )
        if new_part:
            print(f"  Erstellt: {art['partNumber']} - {art['name']}")

# --- Alle Artikel auflisten ---
print("\n=== Alle Artikel ===\n")
all_parts = sevdesk.partHelper.list(active_only=True)

print(f"  {len(all_parts)} aktive Artikel\n")

for p in all_parts[:10]:
    price = p.price or p.priceNet or 0
    tax = p.taxRate or 0
    status = 'Aktiv' if p.status == 100 else 'Inaktiv'
    print(f"  {p.partNumber}: {p.name}")
    print(f"    Preis: {price:,.2f} EUR (MwSt: {tax}%)")
    print(f"    Status: {status}")
    print()

# --- Artikel aktualisieren ---
print("=== Artikel aktualisieren ===\n")

# Preis erhoehen
part = sevdesk.partHelper.find_by_number('CONS-01')
if part:
    old_price = part.price or part.priceNet or 0
    new_price = 160.00

    updated = sevdesk.partHelper.update(
        part_id=int(part.id_),
        price=new_price
    )

    if updated:
        print(f"  Preis aktualisiert: {old_price} -> {new_price} EUR")
    else:
        print("  Fehler beim Aktualisieren")

# --- Suche ---
print("\n=== Artikel suchen ===\n")

# Nach Name suchen
results = sevdesk.partHelper.search('Beratung')
print(f"  Suche 'Beratung': {len(results)} Treffer")
for r in results:
    print(f"    - {r.partNumber}: {r.name}")

# --- Get or Create ---
print("\n=== Get or Create ===\n")

# Holt existierenden oder erstellt neuen Artikel
part = sevdesk.partHelper.get_or_create(
    name='Schulung (Tag)',
    partNumber='TRAIN-01',
    price=1200.00,
    taxRate=19.0,
    unity='tag'
)

if part:
    print(f"  Artikel: {part.partNumber} - {part.name}")
    print(f"  ID: {part.id_}")

# --- Lagerbestand (falls aktiviert) ---
print("\n=== Lagerbestand ===\n")

for p in all_parts[:3]:
    if p.stockEnabled:
        stock = sevdesk.partHelper.get_stock(int(p.id_))
        print(f"  {p.partNumber}: {stock} Stueck")
    else:
        print(f"  {p.partNumber}: Lagerverwaltung deaktiviert")

print("\nSample 09 abgeschlossen!")
