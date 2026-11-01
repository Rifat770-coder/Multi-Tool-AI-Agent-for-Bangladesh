"""Verify pinned sources and atomically rebuild one database at a time."""
import argparse
import hashlib
import csv
import json
import re
import sqlite3
import urllib.request
from contextlib import closing
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
SOURCES = {
    'institutions': ('Institutional-Information-of-Bangladesh', 'data.csv'),
    'hospitals': ('all-bangladeshi-hospitals', 'all-bangladesh-hosptals.csv'),
    'restaurants': ('Bangladeshi-Restaurant-Data', 'restaurants.csv'),
}


def quote(name):
    """Quote a normalized SQLite identifier; identifiers cannot use bind parameters."""
    if not isinstance(name, str) or not re.fullmatch(r'\w+', name):
        raise ValueError('Invalid SQL identifier')
    return '"' + name.replace('"', '""') + '"'


def column_names(headers):
    names = []
    for index, header in enumerate(headers):
        base = re.sub(r'[^\w]+', '_', header.strip().lower()).strip('_') or f'column_{index + 1}'
        name = base
        if base == 'geogrpycal_status':
            name = base = 'geographical_status'
        suffix = 2
        while name in names:
            name = f'{base}_{suffix}'
            suffix += 1
        names.append(name)
    return names


def infer_type(name, values):
    # Identifiers and contact/address strings must retain leading zeroes.
    if name == 'eiin' or any(word in name for word in ('id', 'code', 'phone', 'mobile', 'zip', 'postal', 'fax')):
        return 'TEXT'
    nonempty = [v for v in values if v != '']
    if not nonempty:
        return 'TEXT'
    if any(re.match(r'^[+-]?0\d', v) for v in nonempty):
        return 'TEXT'
    if all(re.fullmatch(r'[+-]?\d+', v) for v in nonempty):
        if all(-(2**63) <= int(v) < 2**63 for v in nonempty):
            return 'INTEGER'
        return 'TEXT'
    if all(re.fullmatch(r'[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?', v) for v in nonempty):
        if name == 'number_of_reviews' and all(float(v).is_integer() and -(2**63) <= float(v) < 2**63 for v in nonempty):
            return 'INTEGER'
        return 'REAL'
    return 'TEXT'


def convert(table, overwrite=False):
    if table not in SOURCES:
        raise ValueError('Unknown dataset')
    metadata = json.loads((Path(__file__).resolve().parents[1] / 'data/sources.json').read_text())[table]
    source = metadata['url']
    db_path = DATA / f'{table}.db'
    if db_path.exists() and not overwrite:
        raise ValueError(f'{db_path} exists; use --overwrite to explicitly replace it.')
    csv_path = DATA / f'{table}.csv'
    if csv_path.exists():
        content = csv_path.read_bytes()
    else:
        request = urllib.request.Request(source, headers={'User-Agent': 'BangladeshAgent/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response:
            content = response.read()
            expected = response.headers.get('Content-Length')
            if expected and len(content) != int(expected):
                raise ValueError(f'{table}: incomplete CSV download')
    if hashlib.sha256(content).hexdigest() != metadata['sha256']:
        raise ValueError(f'{table}: source checksum mismatch; database left unchanged')
    if not csv_path.exists():
        csv_path.write_bytes(content)
    with csv_path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        rows = list(reader)
    if not rows or any(len(row) != len(headers) for row in rows):
        raise ValueError(f'{csv_path}: empty data or inconsistent row widths')
    names = column_names(headers)
    types = [infer_type(name, [row[i] for row in rows]) for i, name in enumerate(names)]
    if any(kind not in ('TEXT', 'INTEGER', 'REAL') for kind in types):
        raise ValueError('Invalid SQLite column type')
    def cast(value, kind):
        if kind == 'TEXT':
            return value
        if value == '':
            return None
        if kind == 'INTEGER':
            return int(value) if re.fullmatch(r'[+-]?\d+', value) else int(float(value))
        return float(value)
    converted = [tuple(cast(v, t) for v, t in zip(row, types)) for row in rows]
    temporary = DATA / f'{table}.db.part'
    with closing(sqlite3.connect(temporary)) as connection, connection:
        # Safe identifier composition: table is allowlisted and quote() validates it.
        # SQLite placeholders bind values, not identifiers. This is sqlite3, not SQLAlchemy.
        # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query
        connection.execute(f'DROP TABLE IF EXISTS {quote(table)}')
        columns = ', '.join(f'{quote(n)} {t}' for n, t in zip(names, types))
        # All names pass quote(); types are restricted to the three literals above.
        # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query
        connection.execute(f'CREATE TABLE {quote(table)} ({columns})')
        placeholders = ', '.join('?' for _ in names)
        connection.executemany(f'INSERT INTO {quote(table)} VALUES ({placeholders})', converted)
        # Only the allowlisted, quoted table name is interpolated; no data values.
        # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query
        actual = connection.execute(f'SELECT * FROM {quote(table)}').fetchall()
        if actual != converted:
            raise AssertionError(f'{table}: source/import mismatch')
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise AssertionError(f'{table}: integrity check failed')
    temporary.replace(db_path)
    return {'source': source, 'sha256': metadata['sha256'], 'revision': metadata['revision'], 'rows': len(rows), 'columns': [
        {'source': h, 'name': n, 'type': t} for h, n, t in zip(headers, names, types)
    ]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rebuild three databases; each file is replaced only after verification.')
    parser.add_argument('--overwrite', action='store_true', help='Replace existing three .db files and schema.json')
    parser.add_argument('--output-dir', type=Path, default=DATA)
    args = parser.parse_args()
    DATA = args.output_dir.resolve()
    DATA.mkdir(parents=True, exist_ok=True)
    if not args.overwrite and any((DATA / f'{t}.db').exists() for t in SOURCES):
        parser.error('Existing databases would be replaced; use --overwrite or a new --output-dir.')
    try:
        report = {table: convert(table, args.overwrite) for table in SOURCES}
    except (OSError, ValueError, csv.Error, StopIteration, sqlite3.Error) as error:
        parser.exit(1, f'Rebuild failed ({type(error).__name__}). Check sources/checksums and output permissions; existing final databases are replaced only after verification.\n')
    (DATA / 'schema.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for table, info in report.items():
        print(f'{table}.db: {info["rows"]} rows; {info["columns"]}')
