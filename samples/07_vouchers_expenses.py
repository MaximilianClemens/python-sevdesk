"""
Sample 07: Voucher/Belege (Ausgaben) verwalten

Voucher in sevDesk sind Eingangsbelege (Eingangsrechnungen, Quittungen, etc.)
- Alle Belege auflisten
- Nach Status filtern (Entwurf, Offen, Bezahlt)
- Ausgaben/Gutschriften getrennt abrufen
- Belege eines Lieferanten
- Positionen eines Belegs
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

# --- Alle Belege auflisten ---
print("=== Alle Belege ===\n")
all_vouchers = sevdesk.voucherHelper.list()

if not all_vouchers:
    print("  Keine Belege gefunden.")
    print("  Hinweis: Belege werden in sevDesk unter")
    print("           Buchhaltung > Belege erfasst.")
else:
    print(f"  {len(all_vouchers)} Beleg(e) gefunden\n")

    # Maximal 5 anzeigen
    for v in all_vouchers[:5]:
        status_label = sevdesk.voucherHelper.get_status_label(v.status)
        gross = float(v.sumGross) if v.sumGross else 0
        supplier = v.supplierName or 'Unbekannt'

        print(f"  ID: {v.id_}")
        print(f"  Beschreibung: {v.description or '-'}")
        print(f"  Lieferant: {supplier}")
        print(f"  Brutto: {gross:,.2f} EUR")
        print(f"  Status: {status_label}")
        print(f"  Datum: {v.voucherDate or '-'}")
        print()

    if len(all_vouchers) > 5:
        print(f"  ... und {len(all_vouchers) - 5} weitere Belege\n")

# --- Gesamtübersicht ---
print("=== Gesamtuebersicht ===\n")
totals = sevdesk.voucherHelper.calculate_totals(all_vouchers)
print(f"  Anzahl Belege: {totals['count']}")
print(f"  Summe Netto:   {totals['net']:>12,.2f} EUR")
print(f"  Summe MwSt:    {totals['tax']:>12,.2f} EUR")
print(f"  Summe Brutto:  {totals['gross']:>12,.2f} EUR")
print(f"  Davon bezahlt: {totals['paid']:>12,.2f} EUR")
print(f"  Offen:         {totals['open']:>12,.2f} EUR")

# --- Nach Status gruppiert ---
print("\n=== Nach Status gruppiert ===\n")
by_status = sevdesk.voucherHelper.group_by_status(all_vouchers)

for status, vouchers in by_status.items():
    label = sevdesk.voucherHelper.get_status_label(status)
    status_totals = sevdesk.voucherHelper.calculate_totals(vouchers)
    print(f"  {label}:")
    print(f"    Anzahl: {status_totals['count']}")
    print(f"    Summe:  {status_totals['gross']:,.2f} EUR")
    print()

# --- Nur offene Belege ---
print("=== Offene Belege (unbezahlt) ===\n")
open_vouchers = sevdesk.voucherHelper.get_open()

if not open_vouchers:
    print("  Keine offenen Belege.")
else:
    print(f"  {len(open_vouchers)} offene(r) Beleg(e):\n")
    for v in open_vouchers[:5]:
        gross = float(v.sumGross) if v.sumGross else 0
        print(f"  - {v.description or v.id_}: {gross:,.2f} EUR ({v.supplierName or 'Unbekannt'})")

# --- Nur bezahlte Belege ---
print("\n=== Bezahlte Belege ===\n")
paid_vouchers = sevdesk.voucherHelper.get_paid()
print(f"  {len(paid_vouchers)} bezahlte(r) Beleg(e)")

# --- Ausgaben (Debit) ---
print("\n=== Ausgaben (Debit) ===\n")
expenses = sevdesk.voucherHelper.get_expenses()
expense_totals = sevdesk.voucherHelper.calculate_totals(expenses)
print(f"  Anzahl: {expense_totals['count']}")
print(f"  Summe:  {expense_totals['gross']:,.2f} EUR")

# --- Gutschriften (Credit) ---
print("\n=== Gutschriften (Credit) ===\n")
credits = sevdesk.voucherHelper.get_credits()
credit_totals = sevdesk.voucherHelper.calculate_totals(credits)
print(f"  Anzahl: {credit_totals['count']}")
print(f"  Summe:  {credit_totals['gross']:,.2f} EUR")

# --- Belege der letzten 30 Tage ---
print("\n=== Belege der letzten 30 Tage ===\n")
recent = sevdesk.voucherHelper.get_recent(days=30)
recent_totals = sevdesk.voucherHelper.calculate_totals(recent)
print(f"  Anzahl: {recent_totals['count']}")
print(f"  Summe:  {recent_totals['gross']:,.2f} EUR")

# --- Nach Lieferant gruppiert ---
print("\n=== Nach Lieferant gruppiert ===\n")
by_supplier = sevdesk.voucherHelper.group_by_supplier(all_vouchers)

# Top 5 Lieferanten nach Anzahl
sorted_suppliers = sorted(by_supplier.items(), key=lambda x: len(x[1]), reverse=True)
for supplier_name, vouchers in sorted_suppliers[:5]:
    supplier_totals = sevdesk.voucherHelper.calculate_totals(vouchers)
    print(f"  {supplier_name}:")
    print(f"    Belege: {supplier_totals['count']}")
    print(f"    Summe:  {supplier_totals['gross']:,.2f} EUR")
    print()

# --- Positionen eines Belegs anzeigen ---
if all_vouchers:
    print("=== Positionen des ersten Belegs ===\n")
    first_voucher = all_vouchers[0]
    positions = sevdesk.voucherHelper.get_positions(int(first_voucher.id_))

    if positions:
        print(f"  Beleg: {first_voucher.description or first_voucher.id_}")
        print(f"  Positionen: {len(positions)}\n")

        for pos in positions:
            net = float(pos.sumNet) if pos.sumNet else 0
            tax_rate = pos.taxRate or '0'
            print(f"  - Netto: {net:,.2f} EUR (MwSt: {tax_rate}%)")
            if pos.comment:
                print(f"    Kommentar: {pos.comment}")
    else:
        print("  Keine Positionen gefunden.")

# --- Zeitraum-Filter Beispiel ---
print("\n=== Belege im aktuellen Monat ===\n")
today = datetime.now()
month_start = today.replace(day=1).strftime("%Y-%m-%d")
month_end = today.strftime("%Y-%m-%d")

monthly_vouchers = sevdesk.voucherHelper.list(
    start_date=month_start,
    end_date=month_end
)
monthly_totals = sevdesk.voucherHelper.calculate_totals(monthly_vouchers)

print(f"  Zeitraum: {month_start} bis {month_end}")
print(f"  Anzahl: {monthly_totals['count']}")
print(f"  Summe:  {monthly_totals['gross']:,.2f} EUR")

print("\nSample 07 abgeschlossen!")
