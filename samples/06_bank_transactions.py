"""
Sample 06: Bankkonten und Transaktionen

- Alle Bankkonten auflisten
- Standard-Bankkonto ermitteln
- Kontostand abrufen
- Transaktionen abrufen (mit Filtern)
- Umsaetze der letzten 30 Tage
- Gutschriften und Belastungen separat
- Summen berechnen
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sevdesk import Client

# .env laden
load_dotenv()

api_key = os.getenv('SEVDESK_API_KEY')
if not api_key:
    raise RuntimeError("SEVDESK_API_KEY nicht in .env gefunden")

sevdesk = Client(api_key)

# --- Alle Bankkonten auflisten ---
print("=== Bankkonten ===\n")
accounts = sevdesk.bankHelper.get_accounts(active_only=True)

if not accounts:
    print("Keine aktiven Bankkonten gefunden.")
    print("Hinweis: Bankkonten werden in sevDesk unter")
    print("         Einstellungen > Bankkonten verwaltet.")
    exit(0)

for account in accounts:
    default_marker = " (Standard)" if str(account.defaultAccount) == '1' else ""
    print(f"  ID: {account.id_}")
    print(f"  Name: {account.name}{default_marker}")
    print(f"  IBAN: {account.iban or '-'}")
    print(f"  Typ: {account.type_ or '-'}")
    print(f"  Waehrung: {account.currency or 'EUR'}")
    print(f"  Status: {'Aktiv' if str(account.status) == '100' else 'Archiviert'}")
    print()

# --- Standard-Bankkonto ermitteln ---
print("=== Standard-Bankkonto ===\n")
default_account = sevdesk.bankHelper.get_default_account()

if default_account:
    print(f"  {default_account.name} (ID: {default_account.id_})")
    account_id = int(default_account.id_)
else:
    print("  Kein Standard-Bankkonto gefunden")
    account_id = int(accounts[0].id_)
    print(f"  Verwende erstes Konto: {accounts[0].name} (ID: {account_id})")

# --- Kontostand abrufen ---
print("\n=== Kontostand ===\n")
today = datetime.now().strftime("%Y-%m-%d")
balance = sevdesk.bankHelper.get_balance(account_id=account_id, date=today)

if balance is not None:
    print(f"  Kontostand am {today}: {balance:,.2f} EUR")
else:
    print(f"  Kontostand konnte nicht ermittelt werden")
    print("  (Moeglicherweise nicht verfuegbar fuer diesen Kontotyp)")

# --- Transaktionen der letzten 30 Tage ---
print("\n=== Transaktionen (letzte 30 Tage) ===\n")
transactions = sevdesk.bankHelper.get_recent_transactions(
    account_id=account_id,
    days=30
)

if not transactions:
    print("  Keine Transaktionen gefunden.")
else:
    print(f"  {len(transactions)} Transaktion(en) gefunden:\n")

    # Maximal 10 anzeigen
    for t in transactions[:10]:
        amount = float(t.amount) if t.amount else 0
        amount_str = f"{amount:+,.2f} EUR"
        date_str = t.valueDate[:10] if t.valueDate else "-"

        # Farbliche Darstellung (+ gruen, - rot) - funktioniert im Terminal
        if amount >= 0:
            amount_display = f"+{amount:,.2f}"
        else:
            amount_display = f"{amount:,.2f}"

        print(f"  {date_str} | {amount_display:>12} EUR | {t.payeePayerName or '-'}")
        if t.paymtPurpose:
            # Verwendungszweck kuerzen
            purpose = t.paymtPurpose[:50] + "..." if len(t.paymtPurpose) > 50 else t.paymtPurpose
            print(f"             {purpose}")
        print()

    if len(transactions) > 10:
        print(f"  ... und {len(transactions) - 10} weitere Transaktionen")

# --- Summen berechnen ---
print("\n=== Zusammenfassung (letzte 30 Tage) ===\n")
sums = sevdesk.bankHelper.sum_transactions(transactions)
print(f"  Eingaenge (Gutschriften): {sums['credits']:>12,.2f} EUR")
print(f"  Ausgaenge (Belastungen):  {sums['debits']:>12,.2f} EUR")
print(f"  ----------------------------------------")
print(f"  Saldo:                    {sums['total']:>12,.2f} EUR")

# --- Nur Gutschriften ---
print("\n=== Nur Gutschriften (letzte 30 Tage) ===\n")
credits = sevdesk.bankHelper.get_credits(
    account_id=account_id,
    start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    end_date=today
)
print(f"  {len(credits)} Gutschrift(en)")

# --- Nur Belastungen ---
print("\n=== Nur Belastungen (letzte 30 Tage) ===\n")
debits = sevdesk.bankHelper.get_debits(
    account_id=account_id,
    start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    end_date=today
)
print(f"  {len(debits)} Belastung(en)")

# --- Suche nach bestimmtem Empfaenger/Zahler ---
print("\n=== Beispiel: Transaktionen nach Zeitraum ===\n")
# Letzten Monat
last_month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1)
last_month_end = datetime.now().replace(day=1) - timedelta(days=1)

print(f"  Zeitraum: {last_month_start.strftime('%Y-%m-%d')} bis {last_month_end.strftime('%Y-%m-%d')}")

last_month_transactions = sevdesk.bankHelper.get_transactions(
    account_id=account_id,
    start_date=last_month_start.strftime("%Y-%m-%d"),
    end_date=last_month_end.strftime("%Y-%m-%d")
)
print(f"  Transaktionen: {len(last_month_transactions)}")

if last_month_transactions:
    sums_last_month = sevdesk.bankHelper.sum_transactions(last_month_transactions)
    print(f"  Eingaenge: {sums_last_month['credits']:,.2f} EUR")
    print(f"  Ausgaenge: {sums_last_month['debits']:,.2f} EUR")

print("\nSample 06 abgeschlossen!")
