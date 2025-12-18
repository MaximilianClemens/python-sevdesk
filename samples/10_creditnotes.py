"""
Sample 10: Gutschriften (CreditNotes) verwalten

- Alle Gutschriften auflisten
- Nach Status filtern
- PDF herunterladen
- Summen berechnen
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

# --- Alle Gutschriften auflisten ---
print("=== Alle Gutschriften ===\n")
creditnotes = sevdesk.creditNoteHelper.list()

if not creditnotes:
    print("  Keine Gutschriften gefunden.")
    print("  Hinweis: Gutschriften entstehen durch Stornierung von Rechnungen")
    print("           oder manuelles Erstellen in sevDesk.")
else:
    print(f"  {len(creditnotes)} Gutschrift(en) gefunden\n")

    for cn in creditnotes[:5]:
        gross = float(cn.sumGross) if cn.sumGross else 0
        status = sevdesk.creditNoteHelper.get_status_label(cn.status)

        print(f"  ID: {cn.id_}")
        print(f"  Nummer: {cn.creditNoteNumber or '-'}")
        print(f"  Kontakt: {cn.contact.id_ if cn.contact else '-'}")
        print(f"  Brutto: {gross:,.2f} EUR")
        print(f"  Status: {status}")
        print()

# --- Nach Status filtern ---
print("=== Nach Status ===\n")

drafts = sevdesk.creditNoteHelper.get_drafts()
print(f"  Entwuerfe: {len(drafts)}")

open_cn = sevdesk.creditNoteHelper.get_open()
print(f"  Offen: {len(open_cn)}")

paid = sevdesk.creditNoteHelper.get_paid()
print(f"  Bezahlt: {len(paid)}")

# --- Letzte 30 Tage ---
print("\n=== Letzte 30 Tage ===\n")
recent = sevdesk.creditNoteHelper.get_recent(days=30)
print(f"  {len(recent)} Gutschrift(en)")

# --- Summen berechnen ---
print("\n=== Gesamtsummen ===\n")
totals = sevdesk.creditNoteHelper.calculate_totals(creditnotes)
print(f"  Anzahl: {totals['count']}")
print(f"  Netto:  {totals['net']:,.2f} EUR")
print(f"  MwSt:   {totals['tax']:,.2f} EUR")
print(f"  Brutto: {totals['gross']:,.2f} EUR")

# --- PDF einer Gutschrift ---
if creditnotes:
    print(f"\n=== PDF von Gutschrift {creditnotes[0].id_} ===\n")
    pdf = sevdesk.creditNoteHelper.get_pdf(int(creditnotes[0].id_))
    if pdf:
        filename = f"gutschrift_{creditnotes[0].id_}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf)
        print(f"  PDF gespeichert: {filename} ({len(pdf)} bytes)")
    else:
        print("  PDF konnte nicht geladen werden")

# --- Gutschrift per Nummer suchen ---
print("\n=== Suche nach Nummer ===\n")
if creditnotes and creditnotes[0].creditNoteNumber:
    cn = sevdesk.creditNoteHelper.find_by_number(creditnotes[0].creditNoteNumber)
    if cn:
        print(f"  Gefunden: {cn.creditNoteNumber} (ID: {cn.id_})")
    else:
        print("  Nicht gefunden")

print("\nSample 10 abgeschlossen!")
