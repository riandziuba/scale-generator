import pytest
import tempfile
import os
import json
from app import app, init_db, DB_PATH, DATA_DIR


@pytest.fixture
def client():
    app.config['TESTING'] = True
    old_db = DB_PATH
    old_data = DATA_DIR
    tmpf = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp = tmpf.name
    tmpf.close()
    tmpdir = tempfile.mkdtemp()
    import app as a
    a.DB_PATH = tmp
    a.DATA_DIR = tmpdir
    os.makedirs(tmpdir, exist_ok=True)
    init_db()
    with app.test_client() as c:
        yield c
    a.DB_PATH = old_db
    a.DATA_DIR = old_data
    if os.path.exists(tmp):
        os.unlink(tmp)
    if os.path.exists(tmpdir):
        os.rmdir(tmpdir)


def test_create_person(client):
    r = client.post('/api/pessoas', json={'name': 'João', 'contact': 'joao@x.com'})
    assert r.status_code == 201
    data = r.get_json()
    assert data['name'] == 'João'
    assert data['contact'] == 'joao@x.com'


def test_create_person_no_name(client):
    r = client.post('/api/pessoas', json={'contact': 'x'})
    assert r.status_code == 400


def test_create_person_empty_name(client):
    r = client.post('/api/pessoas', json={'name': '', 'contact': ''})
    assert r.status_code == 400


def test_list_people(client):
    client.post('/api/pessoas', json={'name': 'A'})
    client.post('/api/pessoas', json={'name': 'B'})
    r = client.get('/api/pessoas')
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 2


def test_update_person(client):
    client.post('/api/pessoas', json={'name': 'Old'})
    r = client.put('/api/pessoas/1', json={'name': 'New', 'contact': 'c'})
    assert r.status_code == 200
    assert r.get_json()['name'] == 'New'


def test_update_missing_person(client):
    r = client.put('/api/pessoas/999', json={'name': 'X', 'contact': ''})
    assert r.status_code == 404


def test_delete_person(client):
    client.post('/api/pessoas', json={'name': 'X'})
    r = client.delete('/api/pessoas/1')
    assert r.status_code == 204
    assert len(client.get('/api/pessoas').get_json()) == 0


def test_add_unavailability(client):
    client.post('/api/pessoas', json={'name': 'Ana'})
    r = client.post('/api/indisponibilidades', json={'person_id': 1, 'date': '2026-07-12'})
    assert r.status_code == 201
    assert r.get_json()['date'] == '2026-07-12'


def test_add_unavailability_missing_person(client):
    r = client.post('/api/indisponibilidades', json={'person_id': 999, 'date': '2026-07-12'})
    assert r.status_code == 400


def test_add_unavailability_invalid_date(client):
    client.post('/api/pessoas', json={'name': 'Ana'})
    r = client.post('/api/indisponibilidades', json={'person_id': 1, 'date': 'not-a-date'})
    assert r.status_code == 400


def test_generate_sunday_scales(client):
    for i in range(4):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    r = client.post('/api/escalas/gerar', json={
        'num_people': 2,
        'start_date': '2026-07-01',
        'end_date': '2026-07-31'
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data['created'] > 0

    scales = client.get('/api/escalas').get_json()
    sundays = [s for s in scales if s['type'] == 'sunday']
    assert len(sundays) == 4


def test_generate_scales_invalid_date(client):
    r = client.post('/api/escalas/gerar', json={
        'num_people': 2,
        'start_date': 'not-date',
        'end_date': '2026-07-31'
    })
    assert r.status_code == 400


def test_generate_scales_invalid_number(client):
    r = client.post('/api/escalas/gerar', json={
        'num_people': -1,
        'start_date': '2026-07-01',
        'end_date': '2026-07-31'
    })
    assert r.status_code == 400


def test_generate_scales_reverse_date(client):
    r = client.post('/api/escalas/gerar', json={
        'num_people': 2,
        'start_date': '2026-07-31',
        'end_date': '2026-07-01'
    })
    assert r.status_code == 400


def test_unavailability_filtering(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/indisponibilidades', json={'person_id': 1, 'date': '2026-07-12'})
    r = client.post('/api/escalas/gerar', json={
        'num_people': 2,
        'start_date': '2026-07-12',
        'end_date': '2026-07-12'
    })
    assert r.status_code == 201
    scales = client.get('/api/escalas').get_json()
    july12 = [s for s in scales if s['date'] == '2026-07-12']
    assert len(july12) == 1
    assigned_ids = [p['id'] for p in july12[0]['assignments']]
    assert 1 not in assigned_ids


def test_extra_day(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    r = client.post('/api/escalas/extra', json={
        'date': '2026-07-15',
        'description': 'Evento',
        'num_people': 2
    })
    assert r.status_code == 201
    scales = client.get('/api/escalas').get_json()
    extras = [s for s in scales if s['type'] == 'extra']
    assert len(extras) == 1
    assert extras[0]['description'] == 'Evento'


def test_extra_day_no_description(client):
    r = client.post('/api/escalas/extra', json={
        'date': '2026-07-15',
        'description': '',
        'num_people': 2
    })
    assert r.status_code == 400


def test_extra_day_invalid_date(client):
    r = client.post('/api/escalas/extra', json={
        'date': 'bad',
        'description': 'Evento',
        'num_people': 2
    })
    assert r.status_code == 400


def test_extra_day_duplicate(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/extra', json={
        'date': '2026-07-15', 'description': 'E1', 'num_people': 2
    })
    r = client.post('/api/escalas/extra', json={
        'date': '2026-07-15', 'description': 'E2', 'num_people': 2
    })
    assert r.status_code == 400


def test_delete_scale(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    r = client.delete(f'/api/escalas/{sid}')
    assert r.status_code == 204
    assert len(client.get('/api/escalas').get_json()) == 0


def test_regenerate_scale(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    r = client.post(f'/api/escalas/{sid}/regenerar')
    assert r.status_code == 200


def test_regenerate_missing_scale(client):
    r = client.post('/api/escalas/999/regenerar')
    assert r.status_code == 404


def test_create_rehearsal(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    pid = scales[0]['assignments'][0]['id']
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '19:00', 'person_id': pid
    })
    assert r.status_code == 201
    assert r.get_json()['time'] == '19:00'


def test_create_rehearsal_invalid_time(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    pid = scales[0]['assignments'][0]['id']
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '25:00', 'person_id': pid
    })
    assert r.status_code == 400


def test_create_rehearsal_missing_scale(client):
    r = client.post('/api/ensaios', json={
        'scale_id': 999, 'date': '2026-07-04', 'time': '19:00', 'person_id': 1
    })
    assert r.status_code == 404


def test_update_rehearsal(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    pid = scales[0]['assignments'][0]['id']
    client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '19:00', 'person_id': pid
    })
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-05', 'time': '20:00', 'person_id': pid
    })
    assert r.status_code == 201
    assert r.get_json()['time'] == '20:00'


def test_delete_rehearsal(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    pid = scales[0]['assignments'][0]['id']
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '19:00', 'person_id': pid
    })
    eid = r.get_json()['id']
    r = client.delete(f'/api/ensaios/{eid}')
    assert r.status_code == 204
    assert len(client.get('/api/ensaios').get_json()) == 0


def test_sunday_scale_no_repeat_next_week(client):
    for i in range(6):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 3,
        'start_date': '2026-08-01',
        'end_date': '2026-08-31'
    })
    scales = client.get('/api/escalas').get_json()
    scales.sort(key=lambda x: x['date'])
    sundays = [s for s in scales if s['type'] == 'sunday']
    for i in range(1, len(sundays)):
        prev_ids = {p['id'] for p in sundays[i - 1]['assignments']}
        curr_ids = {p['id'] for p in sundays[i]['assignments']}
        if len(prev_ids) + len(curr_ids) <= 6:
            assert prev_ids.isdisjoint(curr_ids), \
                f'Week {i} repeats from week {i-1}: {prev_ids & curr_ids}'


def test_rehearsal_nonexistent_person(client):
    for i in range(3):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '19:00', 'person_id': 999
    })
    assert r.status_code == 400


def test_rehearsal_person_not_assigned(client):
    for i in range(4):
        client.post('/api/pessoas', json={'name': f'P{i}'})
    client.post('/api/escalas/gerar', json={
        'num_people': 2, 'start_date': '2026-07-01', 'end_date': '2026-07-05'
    })
    scales = client.get('/api/escalas').get_json()
    sid = scales[0]['id']
    assigned_ids = {p['id'] for p in scales[0]['assignments']}
    unassigned = [pid for pid in range(1, 5) if pid not in assigned_ids][0]
    r = client.post('/api/ensaios', json={
        'scale_id': sid, 'date': '2026-07-04', 'time': '19:00', 'person_id': unassigned
    })
    assert r.status_code == 400


def test_migration_from_old_schema(client):
    import app as a
    import sqlite3
    conn = sqlite3.connect(a.DB_PATH)
    conn.executescript('''
        DROP TABLE IF EXISTS rehearsals;
        DROP TABLE IF EXISTS scale_assignments;
        DROP TABLE IF EXISTS scales;
        DROP TABLE IF EXISTS unavailability;
        DROP TABLE IF EXISTS people;
        CREATE TABLE pessoas (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, contato TEXT DEFAULT '');
        CREATE TABLE indisponibilidades (id INTEGER PRIMARY KEY, pessoa_id INTEGER NOT NULL, data DATE NOT NULL);
        CREATE TABLE escalas (id INTEGER PRIMARY KEY, data DATE NOT NULL, descricao TEXT DEFAULT '', tipo TEXT NOT NULL DEFAULT 'domingo', numero_pessoas INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE escalados (id INTEGER PRIMARY KEY, escala_id INTEGER NOT NULL, pessoa_id INTEGER NOT NULL);
        CREATE TABLE ensaios (id INTEGER PRIMARY KEY, data DATE NOT NULL, horario TEXT NOT NULL DEFAULT '09:00', pessoa_id INTEGER, escala_id INTEGER);
        INSERT INTO pessoas (nome, contato) VALUES ('Miguel', 'm@x.com'), ('Ana', 'a@x.com');
        INSERT INTO escalas (data, tipo, numero_pessoas) VALUES ('2026-07-05', 'domingo', 2);
        INSERT INTO escalados (escala_id, pessoa_id) VALUES (1, 1), (1, 2);
        INSERT INTO ensaios (data, horario, pessoa_id, escala_id) VALUES ('2026-07-04', '18:00', 1, 1);
    ''')
    conn.commit()
    conn.close()

    a.init_db()

    r = client.get('/api/pessoas')
    data = r.get_json()
    assert len(data) == 2
    assert data[0]['name'] in ('Miguel', 'Ana')

    r = client.get('/api/escalas')
    scales = r.get_json()
    assert len(scales) >= 1
    assert scales[0]['type'] == 'sunday'
    assert len(scales[0]['assignments']) == 2

    r = client.get('/api/ensaios')
    rehearsals = r.get_json()
    assert len(rehearsals) >= 1
    assert rehearsals[0]['time'] == '18:00'
