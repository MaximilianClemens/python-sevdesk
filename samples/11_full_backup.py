"""
Sample 11: Vollexport (rein lesend)

- Beleg-ZIPs pro Monat und gesamt, Beleglisten, CSV-Exporte
- Roh-JSON aller Modelle (Belege, Positionen, Bank, Kontakte, Konten, UStVA)
- Original-Belege, UStVA-Protokolle und Rechnungs-PDFs einzeln
- manifest.json mit SHA-256, Abgleich und Kontrollsummen
"""

import os
from dotenv import load_dotenv
from sevdesk import Client

load_dotenv()

api_key = os.getenv('SEVDESK_API_KEY')
if not api_key:
    raise RuntimeError("SEVDESK_API_KEY nicht in .env gefunden")

sevdesk = Client(api_key)

report = sevdesk.backupHelper.run('./export', start_year=2025)

check = report['abgleich']
print(f"Belege laut API: {check['belege_api']}")
print(f"Belegdateien: {check['belegdateien_einzeln']} von {check['belege_mit_dokument']} mit Dokument")
for failure in report['fehler']:
    print(f"Fehler: {failure['step']}: {failure['error']}")
