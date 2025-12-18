# AGENTS.md - sevDesk API Client

## Projektbeschreibung

Inoffizieller Python-Client fuer die sevDesk Buchhaltungs-API. Generiert Models/Controller aus OpenAPI-Spec, erweitert um High-Level Helper.

## Tech Stack

- Python 3.8+
- Pydantic (Models)
- Requests (HTTP)
- Jinja2 (Code-Generator)

## Architektur

### Zwei API-Ebenen

1. **Low-Level (generiert)**: Direkter API-Zugriff via Controller
   - `client.contact.getContacts()`
   - `client.invoice.getInvoices()`

2. **High-Level (manuell)**: Helper mit vereinfachter API
   - `client.contactHelper.find_by_mail()`
   - `client.invoiceHelper.new().addPosition().save()`

### Verzeichnisstruktur

```
sevdesk/
  controllers/      # GENERIERT - nicht manuell aendern
  models/           # GENERIERT - nicht manuell aendern
  converters/       # GENERIERT - nicht manuell aendern
  helpers/          # MANUELL - High-Level API
  helpermodels/     # MANUELL - Erweiterte Models
  undocumented/     # MANUELL - Nicht in OpenAPI dokumentierte Endpoints
    controllers/
    models/
  base/             # BaseController mit Decorator-Pattern
  client.py         # Client-Klasse, laedt Controller automatisch

generator/
  __main__.py       # Generator-Logik
  patches.yaml      # Fixes fuer OpenAPI-Fehler
  *.jinja           # Templates

samples/            # Ausfuehrbare Beispiele mit .env
```

## Wichtige Patterns

### Controller-Decorator

Controller nutzen Generator-Pattern mit `yield`:

```python
class InvoiceController(BaseController):
    @BaseController.get("/Invoice")
    def getInvoices(self, status: Optional[float] = None) -> list[InvoiceResponse]:
        return (yield)
```

### Helper-Pattern

Helper wrappen Controller fuer einfache Nutzung:

```python
class InvoiceHelper:
    def new(self, contact, ...) -> InvoiceExt:
        invoice = InvoiceExt(...)
        invoice._set_client(self.client)
        return invoice
```

### Undocumented API

Fuer Endpoints die nicht in der offiziellen OpenAPI-Spec sind:

```python
# Zugriff via client.undocumented.{controller}
client.undocumented.letter.createLetter(body=letter)
client.undocumented.sevuser.getSevUsers()
```

## Generator

OpenAPI-Spec: https://api.sevdesk.de/openapi.yaml

```bash
curl -o openapi.yaml https://api.sevdesk.de/openapi.yaml
python -m generator
```

**Patches** (`generator/patches.yaml`): Korrigiert Fehler in der offiziellen Spec (z.B. falsche Typen).

## Konventionen

- Generierte Dateien (`controllers/`, `models/`, `converters/`) NIE manuell aendern
- Manuelle Erweiterungen in `helpers/`, `helpermodels/`, `undocumented/`
- Samples nutzen `load_dotenv()` und `.env` fuer API-Key
- Deutsche Kommentare in manuellen Dateien OK

## Bekannte Eigenheiten

- `contactPerson_id` (SevUser) ist bei Dokumenten required, wird aber automatisch ermittelt
- Manche Response-Felder sind als `str` statt `int` typisiert (API-Inkonsistenz)
- Letter-API ist undocumented, funktioniert aber

## Typische Aufgaben

### Neuen Helper hinzufuegen

1. Datei in `sevdesk/helpers/` erstellen
2. In `sevdesk/helpers/__init__.py` exportieren
3. In `sevdesk/client.py` als Attribut hinzufuegen
4. Sample in `samples/` erstellen

### Neuen undocumented Controller

1. Datei in `sevdesk/undocumented/controllers/` erstellen
2. Decorator-Pattern mit `@BaseController.get/post/put/delete`
3. Wird automatisch via `client.undocumented.{name}` geladen

### OpenAPI-Fehler fixen

1. Patch in `generator/patches.yaml` hinzufuegen
2. Generator neu ausfuehren
