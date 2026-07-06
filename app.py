from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import sys
import webbrowser
import threading
import socket
from datetime import datetime, timedelta
import random
import re

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def resource_path(relative_path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


DATA_DIR = os.path.join(os.path.expanduser('~'), '.scale-generator')
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'escala.db')

app = Flask(__name__,
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate_old_schema(conn):
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pessoas'"
    )
    if not cursor.fetchone():
        return
    conn.execute(
        "INSERT INTO people (name, contact) SELECT nome, contato FROM pessoas"
    )
    conn.execute(
        "INSERT INTO unavailability (person_id, date) SELECT pessoa_id, data FROM indisponibilidades"
    )
    conn.execute(
        "INSERT INTO scales (date, description, type, num_people) "
        "SELECT data, descricao, CASE WHEN tipo='domingo' THEN 'sunday' ELSE tipo END, numero_pessoas "
        "FROM escalas"
    )
    conn.execute(
        "INSERT INTO scale_assignments (scale_id, person_id) "
        "SELECT escala_id, pessoa_id FROM escalados"
    )
    conn.execute(
        "INSERT INTO rehearsals (date, time, person_id, scale_id) "
        "SELECT data, horario, pessoa_id, escala_id FROM ensaios"
    )
    conn.execute("DROP TABLE IF EXISTS ensaios")
    conn.execute("DROP TABLE IF EXISTS escalados")
    conn.execute("DROP TABLE IF EXISTS escalas")
    conn.execute("DROP TABLE IF EXISTS indisponibilidades")
    conn.execute("DROP TABLE IF EXISTS pessoas")
    conn.commit()


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS unavailability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            date DATE NOT NULL,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS scales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            description TEXT DEFAULT '',
            type TEXT NOT NULL DEFAULT 'sunday',
            num_people INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS scale_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scale_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            FOREIGN KEY (scale_id) REFERENCES scales(id) ON DELETE CASCADE,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS rehearsals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            time TEXT NOT NULL DEFAULT '09:00',
            person_id INTEGER,
            scale_id INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE SET NULL,
            FOREIGN KEY (scale_id) REFERENCES scales(id) ON DELETE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_scales_date_type ON scales(date, type);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rehearsal_scale ON rehearsals(scale_id);
    ''')
    conn.commit()
    migrate_old_schema(conn)
    conn.close()


def get_previous_scale_people(conn, current_date):
    prev = conn.execute(
        'SELECT id FROM scales WHERE date < ? ORDER BY date DESC LIMIT 1',
        (current_date.isoformat(),)
    ).fetchone()
    if not prev:
        return set()
    people = conn.execute(
        'SELECT person_id FROM scale_assignments WHERE scale_id = ?',
        (prev['id'],)
    ).fetchall()
    return set(p['person_id'] for p in people)


def assign_people_to_scale(conn, scale_id, date, num_people, avoid_ids=None):
    conn.execute('DELETE FROM scale_assignments WHERE scale_id = ?', (scale_id,))

    people = conn.execute('SELECT id FROM people').fetchall()
    if not people:
        return

    unavailable = conn.execute(
        'SELECT person_id FROM unavailability WHERE date = ?',
        (date.isoformat(),)
    ).fetchall()
    unavailable_ids = set(u['person_id'] for u in unavailable)

    if avoid_ids is None:
        avoid_ids = set()

    all_available = [p['id'] for p in people if p['id'] not in unavailable_ids]

    preferred = [pid for pid in all_available if pid not in avoid_ids]
    fallback = [pid for pid in all_available if pid in avoid_ids]

    random.shuffle(preferred)
    random.shuffle(fallback)

    to_assign = preferred[:num_people]
    if len(to_assign) < num_people:
        remaining = num_people - len(to_assign)
        to_assign.extend(fallback[:remaining])

    for person_id in to_assign:
        conn.execute(
            'INSERT INTO scale_assignments (scale_id, person_id) VALUES (?, ?)',
            (scale_id, person_id)
        )


def validate_date(iso_str):
    if not isinstance(iso_str, str) or not DATE_RE.match(iso_str):
        return False, 'error_invalid_date_format'
    try:
        datetime.strptime(iso_str, '%Y-%m-%d')
        return True, None
    except ValueError:
        return False, 'error_invalid_date'


def validate_positive_int(value):
    try:
        v = int(value)
        if v < 1:
            return False, 'error_must_be_positive'
        return True, v
    except (TypeError, ValueError):
        return False, 'error_must_be_integer'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/pessoas', methods=['GET', 'POST'])
def api_pessoas():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT id, name, contact FROM people ORDER BY name').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    else:
        data = request.json
        if not data or not isinstance(data.get('name'), str) or not data['name'].strip():
            conn.close()
            return jsonify({'error': 'error_name_required'}), 400
        name = data['name'].strip()
        contact = data.get('contact', '')
        if not isinstance(contact, str):
            contact = ''
        c = conn.execute(
            'INSERT INTO people (name, contact) VALUES (?, ?)',
            (name, contact)
        )
        conn.commit()
        person_id = c.lastrowid
        person = conn.execute('SELECT id, name, contact FROM people WHERE id = ?', (person_id,)).fetchone()
        conn.close()
        return jsonify(dict(person)), 201


@app.route('/api/pessoas/<int:id>', methods=['DELETE', 'PUT'])
def api_pessoa(id):
    conn = get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM people WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return '', 204
    else:
        data = request.json
        if not data or not isinstance(data.get('name'), str) or not data['name'].strip():
            conn.close()
            return jsonify({'error': 'error_name_required'}), 400
        name = data['name'].strip()
        contact = data.get('contact', '')
        if not isinstance(contact, str):
            contact = ''
        conn.execute(
            'UPDATE people SET name = ?, contact = ? WHERE id = ?',
            (name, contact, id)
        )
        conn.commit()
        person = conn.execute('SELECT id, name, contact FROM people WHERE id = ?', (id,)).fetchone()
        conn.close()
        if not person:
            return jsonify({'error': 'error_person_not_found'}), 404
        return jsonify(dict(person))


@app.route('/api/indisponibilidades', methods=['GET', 'POST'])
def api_indisponibilidades():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('''
            SELECT u.id, u.person_id, u.date, p.name as person_name
            FROM unavailability u
            JOIN people p ON p.id = u.person_id
            ORDER BY u.date, p.name
        ''').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    else:
        data = request.json
        if not data:
            conn.close()
            return jsonify({'error': 'error_empty_body'}), 400

        valid_date, date_err = validate_date(data.get('date', ''))
        if not valid_date:
            conn.close()
            return jsonify({'error': date_err}), 400

        try:
            person_id = int(data['person_id'])
        except (TypeError, ValueError, KeyError):
            conn.close()
            return jsonify({'error': 'error_pessoa_id_number'}), 400

        try:
            c = conn.execute(
                'INSERT INTO unavailability (person_id, date) VALUES (?, ?)',
                (person_id, data['date'])
            )
            conn.commit()
            new = conn.execute('''
                SELECT u.id, u.person_id, u.date, p.name as person_name
                FROM unavailability u
                JOIN people p ON p.id = u.person_id
                WHERE u.id = ?
            ''', (c.lastrowid,)).fetchone()
            conn.close()
            return jsonify(dict(new)), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'error_person_not_found'}), 400


@app.route('/api/indisponibilidades/<int:id>', methods=['DELETE'])
def api_indisponibilidade(id):
    conn = get_db()
    conn.execute('DELETE FROM unavailability WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/api/escalas/gerar', methods=['POST'])
def gerar_escalas():
    data = request.json
    if not data:
        return jsonify({'error': 'error_empty_body'}), 400

    ok, num = validate_positive_int(data.get('num_people'))
    if not ok:
        return jsonify({'error': num}), 400

    valid_ini, err_ini = validate_date(data.get('start_date', ''))
    if not valid_ini:
        return jsonify({'error': err_ini}), 400
    valid_fim, err_fim = validate_date(data.get('end_date', ''))
    if not valid_fim:
        return jsonify({'error': err_fim}), 400

    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

    if start_date > end_date:
        return jsonify({'error': 'error_data_inicio_before_fim'}), 400

    conn = get_db()

    current = start_date
    days_ahead = 6 - current.weekday()
    if days_ahead < 0:
        days_ahead += 7
    current += timedelta(days=days_ahead)

    created = []
    skipped = []
    previous_avoid = get_previous_scale_people(conn, current)

    while current <= end_date:
        existing = conn.execute(
            'SELECT id, num_people FROM scales WHERE date = ? AND type = "sunday"',
            (current.isoformat(),)
        ).fetchone()

        if not existing:
            c = conn.execute(
                'INSERT INTO scales (date, description, type, num_people) VALUES (?, ?, ?, ?)',
                (current.isoformat(), '', 'sunday', num)
            )
            scale_id = c.lastrowid
            assign_people_to_scale(conn, scale_id, current, num, previous_avoid)
            created.append(scale_id)
        else:
            skipped.append(current.isoformat())
            scale_id = existing['id']

        scale_people = conn.execute(
            'SELECT person_id FROM scale_assignments WHERE scale_id = ?',
            (scale_id,)
        ).fetchall()
        previous_avoid = set(p['person_id'] for p in scale_people)

        current += timedelta(days=7)

    conn.commit()
    conn.close()

    msg = f'{len(created)} scale(s) created'
    if skipped:
        msg += f', {len(skipped)} already existed and were skipped'
    return jsonify({'created': len(created), 'skipped': skipped, 'message': msg}), 201


@app.route('/api/escalas', methods=['GET'])
def listar_escalas():
    conn = get_db()
    scales = conn.execute('SELECT * FROM scales ORDER BY date DESC').fetchall()
    result = []
    for scale in scales:
        d = dict(scale)
        assignments = conn.execute('''
            SELECT p.id, p.name
            FROM scale_assignments sa
            JOIN people p ON p.id = sa.person_id
            WHERE sa.scale_id = ?
        ''', (scale['id'],)).fetchall()
        d['assignments'] = [dict(a) for a in assignments]

        rehearsal = conn.execute('''
            SELECT r.*, p.name as person_name
            FROM rehearsals r
            LEFT JOIN people p ON p.id = r.person_id
            WHERE r.scale_id = ?
        ''', (scale['id'],)).fetchone()
        d['rehearsal'] = dict(rehearsal) if rehearsal else None

        result.append(d)

    conn.close()
    return jsonify(result)


@app.route('/api/escalas/<int:id>', methods=['DELETE'])
def deletar_escala(id):
    conn = get_db()
    conn.execute('DELETE FROM scales WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/api/escalas/<int:id>/regenerar', methods=['POST'])
def regenerar_escala(id):
    conn = get_db()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (id,)).fetchone()
    if not scale:
        conn.close()
        return jsonify({'error': 'error_scale_not_found'}), 404

    date = datetime.strptime(scale['date'], '%Y-%m-%d').date()
    avoid_ids = get_previous_scale_people(conn, date)
    assign_people_to_scale(conn, id, date, scale['num_people'], avoid_ids)
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/escalas/extra', methods=['POST'])
def criar_extra():
    data = request.json
    if not data:
        return jsonify({'error': 'error_empty_body'}), 400

    valid_date, date_err = validate_date(data.get('date', ''))
    if not valid_date:
        return jsonify({'error': date_err}), 400

    ok, num = validate_positive_int(data.get('num_people'))
    if not ok:
        return jsonify({'error': num}), 400

    description = data.get('description', '')
    if not isinstance(description, str) or not description.strip():
        return jsonify({'error': 'error_description_required'}), 400

    conn = get_db()

    existing = conn.execute(
        'SELECT id FROM scales WHERE date = ? AND type = ?',
        (data['date'], 'extra')
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'error_extra_scale_exists'}), 400

    c = conn.execute(
        'INSERT INTO scales (date, description, type, num_people) VALUES (?, ?, ?, ?)',
        (data['date'], description.strip(), 'extra', num)
    )
    scale_id = c.lastrowid
    scale_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    avoid_ids = get_previous_scale_people(conn, scale_date)
    assign_people_to_scale(conn, scale_id, scale_date, num, avoid_ids)
    conn.commit()
    conn.close()
    return jsonify({'id': scale_id}), 201


@app.route('/api/ensaios', methods=['GET', 'POST'])
def api_ensaios():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('''
            SELECT r.*, p.name as person_name, s.date as scale_date
            FROM rehearsals r
            JOIN scales s ON s.id = r.scale_id
            LEFT JOIN people p ON p.id = r.person_id
            ORDER BY r.date DESC
        ''').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    else:
        data = request.json
        if not data:
            conn.close()
            return jsonify({'error': 'error_empty_body'}), 400

        valid_date, date_err = validate_date(data.get('date', ''))
        if not valid_date:
            conn.close()
            return jsonify({'error': date_err}), 400

        time_val = data.get('time', '')
        if not isinstance(time_val, str) or not re.match(r'^\d{2}:\d{2}$', time_val):
            conn.close()
            return jsonify({'error': 'error_invalid_time_format'}), 400
        h, m = time_val.split(':')
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            conn.close()
            return jsonify({'error': 'error_invalid_time_range'}), 400

        try:
            scale_id = int(data['scale_id'])
        except (TypeError, ValueError, KeyError):
            conn.close()
            return jsonify({'error': 'error_escala_id_number'}), 400

        person_id = None
        if data.get('person_id'):
            try:
                person_id = int(data['person_id'])
            except (TypeError, ValueError):
                conn.close()
                return jsonify({'error': 'error_pessoa_id_number'}), 400

        scale = conn.execute('SELECT id FROM scales WHERE id = ?', (scale_id,)).fetchone()
        if not scale:
            conn.close()
            return jsonify({'error': 'error_scale_not_found'}), 404

        if person_id is not None:
            person = conn.execute('SELECT id FROM people WHERE id = ?', (person_id,)).fetchone()
            if not person:
                conn.close()
                return jsonify({'error': 'error_person_not_found'}), 400
            assigned = conn.execute(
                'SELECT id FROM scale_assignments WHERE scale_id = ? AND person_id = ?',
                (scale_id, person_id)
            ).fetchone()
            if not assigned:
                conn.close()
                return jsonify({'error': 'error_person_not_assigned'}), 400

        existing = conn.execute(
            'SELECT id FROM rehearsals WHERE scale_id = ?',
            (scale_id,)
        ).fetchone()

        if existing:
            conn.execute(
                'UPDATE rehearsals SET date = ?, time = ?, person_id = ? WHERE id = ?',
                (data['date'], time_val, person_id, existing['id'])
            )
            rehearsal_id = existing['id']
        else:
            c = conn.execute(
                'INSERT INTO rehearsals (date, time, person_id, scale_id) VALUES (?, ?, ?, ?)',
                (data['date'], time_val, person_id, scale_id)
            )
            rehearsal_id = c.lastrowid

        conn.commit()
        rehearsal = conn.execute('''
            SELECT r.*, p.name as person_name, s.date as scale_date
            FROM rehearsals r
            JOIN scales s ON s.id = r.scale_id
            LEFT JOIN people p ON p.id = r.person_id
            WHERE r.id = ?
        ''', (rehearsal_id,)).fetchone()
        conn.close()
        return jsonify(dict(rehearsal)), 201


@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    threading.Timer(0.5, os._exit, args=[0]).start()
    return jsonify({'status': 'ok'})


@app.route('/api/ensaios/<int:id>', methods=['DELETE'])
def deletar_ensaio(id):
    conn = get_db()
    conn.execute('DELETE FROM rehearsals WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204


def find_free_port(start=5500, max_attempts=20):
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start


def open_browser(port):
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()


if __name__ == '__main__':
    init_db()
    port = find_free_port()
    open_browser(port)
    app.run(debug=False, port=port)
