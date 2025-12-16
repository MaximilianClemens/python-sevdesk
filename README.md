# sevDesk API Client (Inoffiziell)

Ein Python-Client für die sevDesk API, automatisch generiert aus der OpenAPI-Spezifikation. Dies ist notwendig, da sich die sevdesk-Spezifikation mit dem Standard OpenApi-Generator nicht parsen lässt.

## ⚠️ Wichtige Hinweise

- **Dies ist KEINE offizielle sevDesk Library**
- Ich arbeite nicht für sevDesk und bin nicht mit sevDesk verbunden
- **Nutzung auf eigene Gefahr**
- Keine Garantie für Funktionalität oder Vollständigkeit
- Bei Problemen mit Markenrechten oder dem Library-Namen kontaktieren Sie mich bitte
- Falls sich offizielle Vertreter von sevDesk am Namen der Library stören, bin ich bereit, diesen zu übertragen oder die Library unter einem anderen Namen zu veröffentlichen

## Installation

```bash
pip install sevdesk
```

## Quick Start

```python
from sevdesk import Client
from datetime import datetime

# Client initialisieren
client = Client('your-api-token')

# Kontakt suchen oder erstellen
contact = client.contactHelper.find_by_mail('max@example.com')
if not contact:
    contact = client.contactHelper.create(
        name='Max Mustermann',
        email='max@example.com'
    )

# Rechnung mit Positionen erstellen
invoice = client.invoiceHelper.new(
    contact=contact,
    invoiceNumber='REC-2024-001',
    invoiceDate=datetime.now().isoformat()
)

# Positionen hinzufügen
invoice.addPosition('Consulting', quantity=10, price=150.00, taxRate=19.0)

# Speichern und PDF generieren
invoice.save(status='100')  # 100 = Draft
invoice.render()

print(f"✅ Rechnung erstellt: ID {invoice._saved_id}")
```

Siehe `/samples/` für mehr Beispiele!

## Anforderungen

- Python 3.8+
- pydantic
- requests
- pyyaml
- jinja2

## Verwendung

### Client initialisieren

```python
from sevdesk import Client

# API Token von sevDesk Dashboard holen
client = Client('your-api-token-here')
```

### Kontakte abrufen

```python
# Alle Kontakte abrufen
contacts = client.contact.getContacts()

for contact in contacts:
    print(f"ID: {contact.id_}")
    print(f"Name: {contact.name or f'{contact.surename} {contact.familyname}'}")
    print(f"Kundennummer: {contact.customerNumber}")
    print(f"Status: {contact.status}")
    print("-" * 40)
```

### Neuen Kontakt erstellen

```python
from sevdesk.models.contact import Contact
from sevdesk.converters.category import Category

# Organisation erstellen
company = Contact(
    name="Acme Corporation GmbH",
    category=Category(id_=3, objectName="Category")
)
new_company = client.contact.createContact(body=company)
print(f"Organisation erstellt mit ID: {new_company.id_}")

# Person erstellen
person = Contact(
    surename="Max",
    familyname="Mustermann",
    gender="m",
    category=Category(id_=3, objectName="Category")
)
new_person = client.contact.createContact(body=person)
print(f"Person erstellt mit ID: {new_person.id_}")
```

### Rechnungen abrufen

```python
# Alle Rechnungen abrufen
invoices = client.invoice.getInvoices()

for invoice in invoices:
    print(f"Rechnungsnummer: {invoice.invoiceNumber}")
    print(f"Datum: {invoice.invoiceDate}")
    print(f"Betrag: {invoice.sumGross} {invoice.currency}")
    print(f"Status: {invoice.status}")
    print("-" * 40)
```

### Angebote abrufen

```python
# Alle Angebote abrufen
orders = client.order.getOrders()

for order in orders:
    print(f"Angebotsnummer: {order.orderNumber}")
    print(f"Datum: {order.orderDate}")
    print(f"Betrag: {order.sumGross} {order.currency}")
    print(f"Status: {order.status}")
    print("-" * 40)
```

### Kontakt aktualisieren

```python
from sevdesk.models.contactupdate import ContactUpdate

# Kontakt aktualisieren
update_data = ContactUpdate(
    name="Neue Firma GmbH"
)
updated = client.contact.updateContact(contactId=123456, body=update_data)
print(f"Kontakt aktualisiert: {updated.name}")
```

### Kontakt löschen

```python
# Kontakt löschen
client.contact.deleteContact(contactId=123456)
print("Kontakt gelöscht")
```

## High-Level API (Empfohlen)

Die High-Level API bietet vereinfachte Funktionen für häufige Aufgaben ohne direkte API-Komplexität:

### Kontakt suchen oder erstellen

```python
# Nach E-Mail suchen (mit Deduplizierung)
contact = client.contactHelper.find_by_mail('max@example.com')

# Neuen Kontakt erstellen wenn nicht gefunden
if not contact:
    contact = client.contactHelper.create(
        name='Max Mustermann',
        email='max@example.com',
        surname='Mustermann'
    )

print(f"Kontakt-ID: {contact.id_}")
```

### Nach Custom Field suchen

```python
# Kontakt nach Custom Field suchen
contact = client.contactHelper.find_by_customfield(
    field='revitoid',
    value='1234567890'
)
```

### Rechnung erstellen mit Positionen (Fluent API)

```python
# Einfache Rechnung mit Positionen
invoice = client.invoiceHelper.new(
    contact=contact,
    invoiceNumber='REC-2024-001',
    invoiceDate='2024-01-01'
)

# Positionen hinzufügen (mit Method Chaining)
invoice \
    .addPosition('Consulting', quantity=10, price=150.00, taxRate=19.0) \
    .addPosition('Support', quantity=1, price=500.00, taxRate=19.0) \
    .save(status='100')  # 100 = Draft, 1000 = Abgeschlossen

print(f"Rechnung erstellt: {invoice._saved_id}")
```

### Rechnung abrufen und verwalten

```python
# Nach ID suchen
invoice = client.invoiceHelper.find_by_id(123456)

# Nach Rechnungsnummer suchen
invoice = client.invoiceHelper.find_by_number('REC-2024-001')

# Rechnungen auflisten mit Filter
invoices = client.invoiceHelper.list(
    contact_id=contact.id_,
    status='100',  # Nur Drafts
    limit=10
)

# PDF generieren
invoice.render()
pdf_data = invoice.getPDF(download=True)

# Als versendet markieren
invoice.markAsSent()
```

### Batch-Operationen

```python
# Mehrere Rechnungen in einer Schleife erstellen
for order in orders:
    contact = client.contactHelper.find_by_mail(order['email'])
    if not contact:
        contact = client.contactHelper.create(
            name=order['company'],
            email=order['email']
        )
    
    invoice = client.invoiceHelper.new(
        contact=contact,
        invoiceNumber=order['invoice_num'],
        invoiceDate=datetime.now().isoformat()
    )
    
    for item in order['items']:
        invoice.addPosition(
            name=item['name'],
            quantity=item['qty'],
            price=item['price'],
            taxRate=19.0
        )
    
    invoice.save(status='100')
```

## Verfügbare Controller (Low-Level API)

Der Client lädt automatisch alle verfügbaren Controller aus der OpenAPI-Spezifikation:

- `client.contact` - Kontaktverwaltung
- `client.invoice` - Rechnungsverwaltung
- `client.order` - Angebotsverwaltung
- `client.voucher` - Belegverwaltung
- `client.part` - Artikelverwaltung
- ... und viele mehr

Alle Endpoints sind als Methoden verfügbar und vollständig typisiert für IDE-Unterstützung.

### High-Level Helper

- `client.contactHelper` - Vereinfachte Kontaktoperationen
- `client.invoiceHelper` - Vereinfachte Rechnungsoperationen

## Beispiele und Samples

Im `/samples` Verzeichnis findest du vollständige, ausführbare Beispiele:

1. **`01_simple_invoice.py`** - Einfache Rechnung erstellen
   - Kontakt nach E-Mail suchen/erstellen
   - Rechnung mit einer Position
   - Als Draft speichern
   - PDF generieren

2. **`02_contact_management.py`** - Kontaktverwaltung
   - Nach E-Mail suchen
   - Nach Custom Field suchen
   - Neuen Kontakt erstellen
   - Kontakt per ID abrufen
   - Alle Kontakte auflisten

3. **`03_advanced_invoice.py`** - Erweiterte Rechnungen
   - Rechnung mit mehreren Positionen
   - Fluent API für Method Chaining
   - PDF-Generierung
   - PDF-Download
   - Als versendet markieren
   - Rechnungen filtern und auflisten

4. **`04_batch_operations.py`** - Batch-Verarbeitung
   - Mehrere Rechnungen in einer Schleife erstellen
   - Fehlerbehandlung bei Batch-Operationen
   - Zusammenfassung und Reporting
   - Automatische Kontakterstellung bei Bedarf



Falls sich die sevDesk API ändert:

```bash
# Neue openapi.yaml herunterladen
# Dann Generator ausführen:
python -m generator
```

Dies generiert automatisch:
- Models in `sevdeskapi/models/`
- Converter in `sevdeskapi/converters/`
- Controller in `sevdeskapi/controllers/`

Das wird zeitnah über Github Actions abgebildet!

## Lizenz  / Haftungsausschluss

MIT License - Siehe LICENSE Datei

