"""Download the three assignment CSVs and faithfully import them into SQLite."""
import csv
import json
import re
import sqlite3
import urllib.request
from contextlib import closing
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'
SOURCES = {
    'institutions': ('Institutional-Information-of-Bangladesh', 'data.csv'),
    'hospitals': ('all-bangladeshi-hospitals', 'all-bangladesh-hosptals.csv'),
    'restaurants': ('Bangladeshi-Restaurant-Data', 'restaurants.csv'),
}


def quote(name):
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


def convert(table):
    repo, filename = SOURCES[table]
    source = f'https://huggingface.co/datasets/Mahadih534/{repo}/resolve/main/{filename}'
    csv_path = DATA / f'{table}.csv'
    if not csv_path.exists():
        request = urllib.request.Request(source, headers={'User-Agent': 'Module22Assignment/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response:
            content = response.read()
            expected = response.headers.get('Content-Length')
            if expected and len(content) != int(expected):
                raise ValueError(f'{table}: incomplete CSV download')
        temporary = csv_path.with_suffix('.csv.part')
        temporary.write_bytes(content)
        temporary.replace(csv_path)
    with csv_path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        rows = list(reader)
    if not rows or any(len(row) != len(headers) for row in rows):
        raise ValueError(f'{csv_path}: empty data or inconsistent row widths')
    names = column_names(headers)
    types = [infer_type(name, [row[i] for row in rows]) for i, name in enumerate(names)]
    def cast(value, kind):
        if kind == 'TEXT':
            return value
        if value == '':
            return None
        if kind == 'INTEGER':
            return int(value) if re.fullmatch(r'[+-]?\d+', value) else int(float(value))
        return float(value)
    converted = [tuple(cast(v, t) for v, t in zip(row, types)) for row in rows]
    db_path = DATA / f'{table}.db'
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(f'DROP TABLE IF EXISTS {quote(table)}')
        columns = ', '.join(f'{quote(n)} {t}' for n, t in zip(names, types))
        connection.execute(f'CREATE TABLE {quote(table)} ({columns})')
        placeholders = ', '.join('?' for _ in names)
        connection.executemany(f'INSERT INTO {quote(table)} VALUES ({placeholders})', converted)
        actual = connection.execute(f'SELECT * FROM {quote(table)}').fetchall()
        if actual != converted:
            raise AssertionError(f'{table}: source/import mismatch')
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise AssertionError(f'{table}: integrity check failed')
    return {'source': source, 'rows': len(rows), 'columns': [
        {'source': h, 'name': n, 'type': t} for h, n, t in zip(headers, names, types)
    ]}


if __name__ == '__main__':
    DATA.mkdir(exist_ok=True)
    report = {table: convert(table) for table in SOURCES}
    (DATA / 'schema.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for table, info in report.items():
        print(f'{table}.db: {info["rows"]} rows; {info["columns"]}')
