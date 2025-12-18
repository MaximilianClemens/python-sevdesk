"""
Sample 05: Brief erstellen und PDF holen

- Brief mit HTML-Inhalt erstellen
- Brief speichern (als Draft)
- PDF rendern
- Design-Parameter anpassen (optional)
- PDF herunterladen

HINWEIS: contactPerson_id ist optional! Wenn nicht angegeben,
         wird automatisch der erste SevUser des Accounts verwendet.
"""

import os
from dotenv import load_dotenv
from sevdesk import Client

# .env laden
load_dotenv()

api_key = os.getenv('SEVDESK_API_KEY')
if not api_key:
    raise RuntimeError("SEVDESK_API_KEY nicht in .env gefunden")

# Optional: SevUser-ID (deine Benutzer-ID in sevDesk)
# Wenn nicht gesetzt, wird automatisch der erste User verwendet.
SEV_USER_ID = os.getenv('SEVDESK_USER_ID')
if SEV_USER_ID:
    SEV_USER_ID = int(SEV_USER_ID)
    print(f"Verwende SevUser-ID: {SEV_USER_ID}")
else:
    print("Keine SEVDESK_USER_ID gesetzt - verwende automatisch ersten User")

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

# --- Brief erstellen ---
print("\nErstelle Brief...")

# HTML-Inhalt des Briefes
brief_text = """
<p><strong>Sehr geehrte Damen und Herren,</strong></p>

<p>vielen Dank fuer Ihr Interesse an unseren Dienstleistungen.</p>

<p>Gerne moechten wir Ihnen folgendes Angebot unterbreiten:</p>

<ul>
    <li>Beratungsleistung: 100 EUR/Stunde</li>
    <li>Entwicklung: 80 EUR/Stunde</li>
    <li>Support: 50 EUR/Stunde</li>
</ul>

<p>Bei Fragen stehen wir Ihnen gerne zur Verfuegung.</p>

<p><strong>Mit freundlichen Gruessen</strong><br>
Ihr Team</p>
"""

# Adresse des Empfaengers
empfaenger_adresse = """Test Kunde
Musterstrasse 123
12345 Musterstadt"""

# Brief erstellen - contactPerson_id ist optional!
letter = sevdesk.letterHelper.new(
    contact=contact,
    header="Angebot fuer IT-Dienstleistungen",
    text=brief_text,
    address=empfaenger_adresse,
    contactPerson_id=SEV_USER_ID,  # None wenn nicht gesetzt -> automatisch
    status="100"  # Draft
)

# --- Brief speichern ---
letter.save()
print(f"Brief erstellt (ID: {letter.id})")

# --- PDF rendern ---
print("\nRendere PDF...")
letter.render()
print("  PDF gerendert")

# --- Optional: Design-Parameter anpassen ---
# letter.setParameter('logoSize', '33')
# letter.setParameter('color', '#848484')

# --- PDF herunterladen ---
print("\nLade PDF herunter...")
pdf_content = letter.getPDF()

if pdf_content:
    filename = f"brief_{letter.id}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_content)
    print(f"  PDF gespeichert als: {filename}")
    print(f"  Groesse: {len(pdf_content)} bytes")
else:
    print("  Kein PDF-Inhalt erhalten")

# --- Alle Briefe fuer Kontakt auflisten ---
print(f"\nBriefe fuer Kontakt {contact.id_}:")
letters = sevdesk.letterHelper.list(contact_id=int(contact.id_), limit=5)

for l in letters:
    print(f"  - {l.id_}: {l.header} (Status: {l.status})")

print("\nSample 05 abgeschlossen!")
