"""Vollstaendiger, rein lesender Export eines sevDesk-Accounts.

Alle Requests laufen ueber BackupHelper._get, es gibt hier bewusst keinen
Schreibzugriff. Nicht verwendet werden: enshrineDocuments, updateExportConfig
und Order/getPdf (schreibt den Auftrag laut API-Doku fest).
Jeder Schritt ueberspringt bereits vorhandene Dateien.

DATEV-Exporte (createDatev*ZipExportJob) sind standardmaessig aus: Die API
lehnt sie per GET mit "wrong HTTP Type" ab, obwohl die Spec GET nennt.
"""
import base64
import calendar
import hashlib
import json
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DATEV_SCOPE = 'EXTCD'
BERLIN = ZoneInfo('Europe/Berlin')
TAX_RULE_INPUT = '9'

RAW_MODELS = {
    'vouchers': ('/Voucher', {}),
    'voucherpos': ('/VoucherPos', {}),
    'voucherlog': ('/VoucherLog', {}),
    'checkaccounts': ('/CheckAccount', {}),
    'transactions': ('/CheckAccountTransaction', {}),
    'transactionlog': ('/CheckAccountTransactionLog', {}),
    'contacts': ('/Contact', {'depth': 1}),
    'contactaddresses': ('/ContactAddress', {}),
    'communicationways': ('/CommunicationWay', {}),
    'accountingcontacts': ('/AccountingContact', {}),
    'contactcustomfields': ('/ContactCustomField', {}),
    'contactcustomfieldsettings': ('/ContactCustomFieldSetting', {}),
    'invoices': ('/Invoice', {}),
    'invoicepos': ('/InvoicePos', {}),
    'invoicelog': ('/InvoiceLog', {}),
    'creditnotes': ('/CreditNote', {}),
    'creditnotepos': ('/CreditNotePos', {}),
    'orders': ('/Order', {}),
    'orderpos': ('/OrderPos', {}),
    'parts': ('/Part', {}),
    'tags': ('/Tag', {}),
    'tagrelations': ('/TagRelation', {}),
    'documents': ('/Document', {}),
    'documentfolders': ('/DocumentFolder', {}),
    'vatreports': ('/VatReport', {}),
    'assets': ('/Asset', {}),
    'privatetransactionrules': ('/PrivateTransactionRule', {}),
    'sevclient': ('/SevClient', {}),
    'sevusers': ('/SevUser', {}),
    'taxsets': ('/TaxSet', {}),
    'taxrules': ('/TaxRule', {}),
    'accountingtypes': ('/AccountingType', {}),
    'accountingcharts': ('/AccountingChart', {}),
    'accountsdatev': ('/AccountDatev', {}),
    'unities': ('/Unity', {}),
}

RAW_SINGLE = {
    'receiptguidance_all': '/ReceiptGuidance/forAllAccounts',
    'receiptguidance_expense': '/ReceiptGuidance/forExpense',
    'receiptguidance_revenue': '/ReceiptGuidance/forRevenue',
}

MAGIC = (
    (b'%PDF', 'pdf'),
    (b'\x89PNG', 'png'),
    (b'\xff\xd8\xff', 'jpg'),
    (b'PK\x03\x04', 'zip'),
    (b'GIF8', 'gif'),
    (b'<?xml', 'xml'),
)


def sniff_extension(data, filename=None):
    head = data[:16].lstrip()
    for magic, ext in MAGIC:
        if head.startswith(magic):
            return ext
    suffix = Path(filename or '').suffix.lstrip('.').lower()
    return re.sub(r'[^a-z0-9]', '', suffix) or 'bin'


def safe_name(text, maxlen=50):
    text = re.sub(r'[^\w.-]+', '_', str(text or 'unbekannt'), flags=re.UNICODE).strip('_.')
    return text[:maxlen] or 'unbekannt'


def flatten_query(prefix, value, target=None):
    target = {} if target is None else target
    if isinstance(value, dict):
        for key, sub in value.items():
            flatten_query(f'{prefix}[{key}]', sub, target)
    else:
        target[prefix] = value
    return target


def day_range(first, last):
    """sevQuery-Filter brauchen Unix-Timestamps, ISO-Daten liefern stillschweigend nichts."""
    start = datetime(first.year, first.month, first.day, tzinfo=BERLIN)
    end = datetime(last.year, last.month, last.day, 23, 59, 59, tzinfo=BERLIN)
    return {'startDate': int(start.timestamp()), 'endDate': int(end.timestamp())}


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class BackupHelper:
    def __init__(self, client):
        self.client = client
        self.failures = []

    def _get(self, path, params=None, url=None, raw=False, retries=6):
        target = url or f'{self.client.api_base}{path}'
        headers = {} if url else {'Authorization': self.client.api_token}
        for attempt in range(retries):
            try:
                resp = self.client.session.get(target, params=params, headers=headers, timeout=300)
            except requests.RequestException as exc:
                if attempt == retries - 1:
                    raise RuntimeError(f'{path or "download"}: {type(exc).__name__}') from None
                time.sleep(2 ** attempt)
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == retries - 1:
                    raise RuntimeError(f'{path or "download"}: HTTP {resp.status_code}')
                time.sleep(int(resp.headers.get('Retry-After') or 2 ** attempt))
                continue
            if resp.status_code >= 400:
                raise RuntimeError(f'{path or "download"}: HTTP {resp.status_code}: {self._scrub(resp.text[:200])}')
            return resp if raw else resp.json()

    def _scrub(self, text):
        return text.replace(self.client.api_token, '***')

    def _attempt(self, label, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            self.failures.append({'step': label, 'error': self._scrub(str(exc))})
            print(f'FEHLER {label}: {self._scrub(str(exc))}', flush=True)
            return None

    @staticmethod
    def _decode(payload):
        """Base64-Download-Antwort der sevDesk-API in (bytes, filename) wandeln."""
        obj = payload.get('objects') if isinstance(payload.get('objects'), dict) else payload
        content = obj.get('content')
        if content is None:
            raise RuntimeError('Antwort ohne content')
        data = base64.b64decode(content) if obj.get('base64Encoded', True) else content.encode()
        return data, obj.get('filename')

    def _download_query(self, path, query):
        params = {'download': 'true', **flatten_query('sevQuery', query)}
        resp = self._get(path, params, raw=True)
        if 'json' in resp.headers.get('content-type', '').lower():
            return self._decode(resp.json())
        return resp.content, None

    @staticmethod
    def _write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + '.part')
        tmp.write_bytes(data)
        tmp.replace(path)

    # --- Pakete ---

    def datev_job(self, kind, start, end, target, by_paydate=False, poll=10, max_wait=1800):
        if target.exists():
            return target
        params = {'startDate': int(start.timestamp()), 'endDate': int(end.timestamp()), 'scope': DATEV_SCOPE,
                  'includeEnshrined': 'true'}
        if by_paydate:
            params['exportByPaydate'] = 'true'
        if kind == 'csv':
            path = '/Export/createDatevCsvZipExportJob'
            params['includeDocumentImages'] = 'true'
        else:
            path = '/Export/createDatevXmlZipExportJob'
            params.update(includeDocumentXml='true', includeExportedDocuments='true')
        created = self._get(path, params)
        objects = created.get('objects', created)
        job_id = objects.get('id') or objects.get('jobId') if isinstance(objects, dict) else objects
        deadline = time.time() + max_wait
        last = None
        while time.time() < deadline:
            try:
                info = self._get('/ExportJob/jobDownloadInfo', {'jobId': job_id})['objects']
                info = info[0] if isinstance(info, list) else info
                if info and info.get('link'):
                    self._write(target, self._get(None, url=info['link'], raw=True).content)
                    return target
            except RuntimeError as exc:
                last = exc
            time.sleep(poll)
        raise RuntimeError(f'DATEV-Job {kind} nicht fertig geworden ({last})')

    def fetch_all(self, path, params=None, page=1000):
        rows, offset = [], 0
        while True:
            batch = self._get(path, {**(params or {}), 'limit': page, 'offset': offset})['objects'] or []
            rows.extend(batch)
            if len(batch) < page:
                return rows
            offset += page

    def raw_json(self, out):
        for name, (path, params) in RAW_MODELS.items():
            target = out / 'json' / f'{name}.jsonl'
            if target.exists():
                continue
            rows = self._attempt(f'json:{name}', self.fetch_all, path, params)
            if rows is None:
                continue
            text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
            self._write(target, self._scrub(text).encode())
        for name, path in RAW_SINGLE.items():
            target = out / 'json' / f'{name}.json'
            if target.exists():
                continue
            data = self._attempt(f'json:{name}', self._get, path)
            if data is not None:
                self._write(target, self._scrub(json.dumps(data, ensure_ascii=False, indent=1)).encode())

    def referenced_accounts(self, out):
        """Die /AccountDatev-Liste ist nicht vollstaendig, referenzierte Konten einzeln nachladen."""
        target = out / 'json' / 'accountsdatev.jsonl'
        known = {str(a['id']) for a in self.read_jsonl(out, 'accountsdatev')}
        wanted = {str(p['accountDatev']['id']) for p in self.read_jsonl(out, 'voucherpos') if p.get('accountDatev')}
        for account_id in sorted(wanted - known):
            payload = self._attempt(f'konto:{account_id}', self._get, f'/AccountDatev/{account_id}')
            if payload:
                objects = payload['objects']
                row = objects[0] if isinstance(objects, list) else objects
                with target.open('a') as handle:
                    handle.write(self._scrub(json.dumps(row, ensure_ascii=False)) + '\n')

    def read_jsonl(self, out, name):
        path = out / 'json' / f'{name}.jsonl'
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line]

    def voucher_zips(self, out, start_year, end):
        year, month = start_year, 1
        while (year, month) <= (end.year, end.month):
            target = out / 'belege' / f'{year}-{month:02d}.zip'
            if not target.exists():
                last = date(year, month, calendar.monthrange(year, month)[1])
                query = {'modelName': 'Voucher', 'objectName': 'SevQuery', 'limit': 1000,
                         'filter': day_range(date(year, month, 1), last)}
                result = self._attempt(f'belegzip:{year}-{month:02d}', self._download_query, '/Export/voucherZip', query)
                if result:
                    self._write(target, result[0])
            month += 1
            if month > 12:
                year, month = year + 1, 1
        target = out / 'belege_alle.zip'
        if not target.exists():
            query = {'modelName': 'Voucher', 'objectName': 'SevQuery', 'limit': 10000}
            result = self._attempt('belegzip:alle', self._download_query, '/Export/voucherZip', query)
            if result:
                self._write(target, result[0])

    def query_exports(self, out, start_year, end_year):
        for year in range(start_year, end_year + 1):
            query = {'modelName': 'Voucher', 'objectName': 'SevQuery', 'limit': 10000,
                     'filter': day_range(date(year, 1, 1), date(year, 12, 31))}
            target = out / f'belegliste_{year}.csv'
            if not target.exists():
                result = self._attempt(f'belegliste:{year}', self._download_query, '/Export/voucherListCsv', query)
                if result:
                    self._write(target, result[0])
        for name, path, model in (
            ('kontakte.csv', '/Export/contactListCsv', 'Contact'),
            ('rechnungen.csv', '/Export/invoiceCsv', 'Invoice'),
            ('rechnungen.zip', '/Export/invoiceZip', 'Invoice'),
            ('gutschriften.csv', '/Export/creditNoteCsv', 'CreditNote'),
        ):
            target = out / name
            if not target.exists():
                query = {'modelName': model, 'objectName': 'SevQuery', 'limit': 10000}
                result = self._attempt(f'csv:{name}', self._download_query, path, query)
                if result:
                    self._write(target, result[0])

    def bank_exports(self, out):
        for account in self.read_jsonl(out, 'checkaccounts'):
            target = out / 'bank' / f'umsaetze_{account["id"]}_{safe_name(account.get("name"))}.csv'
            if target.exists():
                continue
            query = {'modelName': 'CheckAccountTransaction', 'objectName': 'SevQuery', 'limit': 100000,
                     'filter': {'checkAccount': {'id': account['id'], 'objectName': 'CheckAccount'}}}
            result = self._attempt(f'bank:{account["id"]}', self._download_query, '/Export/transactionsCsv', query)
            if result:
                self._write(target, result[0])

    def _document(self, doc_id, directory, stem):
        existing = list(directory.glob(f'{stem}.*')) if directory.exists() else []
        existing = [p for p in existing if not p.name.endswith('.part')]
        if existing:
            return existing[0]
        data, filename = self._decode(self._get(f'/Document/{doc_id}/download'))
        target = directory / f'{stem}.{sniff_extension(data, filename)}'
        self._write(target, data)
        return target

    def documents(self, out):
        fetched = set()
        for voucher in self.read_jsonl(out, 'vouchers'):
            ref = voucher.get('document')
            if not ref:
                continue
            day = (voucher.get('voucherDate') or '0000-00-00')[:10]
            supplier = voucher.get('supplierNameAtSave') or voucher.get('supplierName')
            stem = f'{day}_{voucher["id"]}_{safe_name(supplier)}'
            if self._attempt(f'beleg:{voucher["id"]}', self._document, ref['id'], out / 'belege_einzeln', stem):
                fetched.add(str(ref['id']))
        for report in self.read_jsonl(out, 'vatreports'):
            ref = report.get('document')
            if not ref:
                continue
            stem = f'ustva_{report["reportingYear"]}_{report["reportingPeriod"]}_{report["id"]}'
            if self._attempt(f'ustva:{report["id"]}', self._document, ref['id'], out / 'auswertungen', stem):
                fetched.add(str(ref['id']))
        for doc in self.read_jsonl(out, 'documents'):
            if str(doc['id']) not in fetched:
                stem = f'{doc["id"]}_{safe_name(doc.get("filename"))}'
                self._attempt(f'dokument:{doc["id"]}', self._document, doc['id'], out / 'dokumente', stem)

    def invoice_documents(self, out):
        for invoice in self.read_jsonl(out, 'invoices'):
            status = int(to_float(invoice.get('status')))
            if status < 200:  # Entwuerfe nicht rendern, nur JSON
                continue
            stem = f'{(invoice.get("invoiceDate") or "")[:10]}_{invoice["id"]}_{safe_name(invoice.get("invoiceNumber"))}'
            target = out / 'rechnungen_einzeln' / f'{stem}.pdf'
            if not target.exists():
                resp = self._attempt(f'rechnung:{invoice["id"]}', self._get, f'/Invoice/{invoice["id"]}/getPdf',
                                     {'download': 'true', 'preventSendBy': 'true'}, raw=True)
                if resp is not None:
                    data = resp.content
                    if 'json' in resp.headers.get('content-type', '').lower():
                        data = self._decode(resp.json())[0]
                    self._write(target, data)

    # --- Abgleich ---

    def reconcile(self, out):
        vouchers = self.read_jsonl(out, 'vouchers')
        with_document = [v for v in vouchers if v.get('document')]
        files = {p.name.split('_')[1]: p for p in (out / 'belege_einzeln').glob('*_*') if not p.name.endswith('.part')} \
            if (out / 'belege_einzeln').exists() else {}
        def members(path):
            with zipfile.ZipFile(path) as archive:
                return [n for n in archive.namelist() if not n.endswith('/') and archive.getinfo(n).file_size]

        zipped = [n for path in sorted((out / 'belege').glob('*.zip')) for n in members(path)] \
            if (out / 'belege').exists() else []
        complete = members(out / 'belege_alle.zip') if (out / 'belege_alle.zip').exists() else []
        return {
            'belege_api': len(vouchers),
            'belege_mit_dokument': len(with_document),
            'belege_ohne_dokument': [
                {'id': v['id'], 'datum': (v.get('voucherDate') or '')[:10], 'status': v.get('status')}
                for v in vouchers if not v.get('document')],
            'belegdateien_einzeln': len(files),
            'dateien_in_monats_zips': len(zipped),
            'dateien_in_belege_alle_zip': len(complete),
            'fehlende_einzeldateien': [v['id'] for v in with_document if str(v['id']) not in files],
            'belege_nach_status': dict(Counter(str(v.get('status')) for v in vouchers)),
        }

    def tax_sums(self, out, year):
        """USt/VSt je Monat, nach Belegdatum und nach Zahlungsdatum (Ist)."""
        pos_by_voucher = defaultdict(list)
        for pos in self.read_jsonl(out, 'voucherpos'):
            pos_by_voucher[str(pos['voucher']['id'])].append(pos)
        rows = defaultdict(lambda: defaultdict(float))
        for voucher in self.read_jsonl(out, 'vouchers'):
            if int(to_float(voucher.get('status'))) < 100:
                continue
            is_input_tax = str((voucher.get('taxRule') or {}).get('id')) == TAX_RULE_INPUT
            is_revenue = voucher.get('creditDebit') == 'D'
            kind = 'vst' if is_input_tax or not is_revenue else 'ust'
            tax = sum(to_float(p.get('sumTax')) for p in pos_by_voucher[str(voucher['id'])]) \
                if pos_by_voucher[str(voucher['id'])] else to_float(voucher.get('sumTax'))
            if is_input_tax and is_revenue:  # Erstattung mindert die Vorsteuer
                tax = -tax
            for basis, field in (('beleg', 'voucherDate'), ('zahlung', 'payDate')):
                day = voucher.get(field) or ''
                if day[:4] == str(year):
                    rows[day[:7]][f'{kind}_{basis}'] += tax
        for invoice in self.read_jsonl(out, 'invoices'):
            if int(to_float(invoice.get('status'))) < 200:
                continue
            tax = to_float(invoice.get('sumTax'))
            for basis, field in (('beleg', 'invoiceDate'), ('zahlung', 'payDate')):
                day = invoice.get(field) or ''
                if day[:4] == str(year):
                    rows[day[:7]][f'ust_rechnung_{basis}'] += tax
        return {month: {k: round(v, 2) for k, v in sorted(rows[month].items())} for month in sorted(rows)}

    def vat_check(self, out):
        """Vorsteuer je Quartal (Belegdatum) gegen die zuletzt uebermittelte UStVA, Kz 66."""
        latest = {}
        for report in sorted(self.vat_reports(out), key=lambda r: r['gemeldet']):
            if report['testfall'] == '0':
                latest[(report['jahr'], report['periode'])] = report
        result = []
        for (year, period), report in sorted(latest.items()):
            quarter = int(period) - 40
            sums = self.tax_sums(out, year)
            months = [f'{year}-{m:02d}' for m in range(3 * quarter - 2, 3 * quarter + 1)]
            computed = round(sum(sums.get(m, {}).get('vst_beleg', 0) for m in months), 2)
            reported = report['kennzahlen'].get('66', 0)
            result.append({'jahr': year, 'quartal': quarter, 'kz66_uebermittelt': reported, 'vst_belegdatum': computed,
                           'differenz': round(computed - reported, 2)})
        return result

    def vat_reports(self, out):
        return [{
            'jahr': r.get('reportingYear'), 'periode': r.get('reportingPeriod'), 'code': r.get('reportingPeriodCode'),
            'korrigiert': r.get('corrected'), 'testfall': r.get('testCase'), 'ist': r.get('actualTaxation'),
            'gemeldet': (r.get('reportDate') or '')[:10],
            'kennzahlen': json.loads(r['reportingValues']) if r.get('reportingValues') else {},
        } for r in self.read_jsonl(out, 'vatreports')]

    def manifest(self, out):
        rows = []
        for path in sorted(p for p in out.rglob('*') if p.is_file()):
            if path.name in ('manifest.json',) or path.name.endswith('.part'):
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entry = {'datei': str(path.relative_to(out)), 'groesse': path.stat().st_size, 'sha256': digest}
            if path.suffix == '.jsonl':
                entry['datensaetze'] = sum(1 for line in path.read_text().splitlines() if line)
            rows.append(entry)
        return rows

    def run(self, out, start_year, end=None, datev=False):
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        end = end or date.today()

        def utc(y, m, d, h=0, mi=0, s=0):
            return datetime(y, m, d, h, mi, s, tzinfo=timezone.utc)

        for year in range(start_year, end.year + 1) if datev else ():
            first, last = utc(year, 1, 1), utc(year, 12, 31, 23, 59, 59)
            print(f'DATEV {year}', flush=True)
            self._attempt(f'datev_csv:{year}', self.datev_job, 'csv', first, last, out / f'datev_csv_{year}.zip')
            self._attempt(f'datev_csv_paydate:{year}', self.datev_job, 'csv', first, last,
                          out / f'datev_csv_{year}_nach_zahlungsdatum.zip', by_paydate=True)
            self._attempt(f'datev_xml:{year}', self.datev_job, 'xml', first, last, out / f'datev_xml_{year}.zip')
        print('Beleg-ZIPs', flush=True)
        self.voucher_zips(out, start_year, end)
        print('Roh-JSON', flush=True)
        self.raw_json(out)
        self.referenced_accounts(out)
        print('CSV-Exporte', flush=True)
        self.query_exports(out, start_year, end.year)
        self.bank_exports(out)
        print('Einzeldokumente', flush=True)
        self.documents(out)
        self.invoice_documents(out)

        report = {
            'erstellt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'abgleich': self.reconcile(out),
            'kontrollsummen': {str(y): self.tax_sums(out, y) for y in range(start_year, end.year + 1)},
            'ustva_uebermittelt': self.vat_reports(out),
            'ustva_abgleich': self.vat_check(out),
            'fehler': self.failures,
        }
        report['dateien'] = self.manifest(out)
        self._write(out / 'manifest.json', json.dumps(report, ensure_ascii=False, indent=1).encode())
        return report
