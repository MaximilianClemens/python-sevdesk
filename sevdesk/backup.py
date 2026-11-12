"""CLI: python -m sevdesk.backup --out ./export/2026-10-30 --from 2025"""
import argparse
import os

from dotenv import load_dotenv

from sevdesk.client import Client


def main():
    parser = argparse.ArgumentParser(description='Rein lesender Vollexport eines sevDesk-Accounts')
    parser.add_argument('--out', required=True)
    parser.add_argument('--from', dest='start_year', type=int, required=True)
    parser.add_argument('--env', default='.env')
    parser.add_argument('--datev', action='store_true', help='DATEV-Exportjobs versuchen (derzeit von der API abgelehnt)')
    args = parser.parse_args()

    load_dotenv(args.env)
    token = (os.getenv('SEVDESK_API_KEY') or '').strip()
    if not token:
        raise SystemExit('SEVDESK_API_KEY fehlt')

    report = Client(token).backupHelper.run(args.out, args.start_year, datev=args.datev)
    check = report['abgleich']
    print(f'Belege API: {check["belege_api"]}, mit Dokument: {check["belege_mit_dokument"]}, '
          f'Einzeldateien: {check["belegdateien_einzeln"]}, Fehler: {len(report["fehler"])}')


if __name__ == '__main__':
    main()
