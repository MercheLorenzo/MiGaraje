"""Authenticated API integration using the public router and a mocked service network."""
import copy

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import insights, resources
from app.db.session import Base, get_db
from app.main import app


def test_swagger_payloads_work_for_crud_and_ownership(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    state = {'vehicles': {}, 'maintenances': {}, 'rules': {}, 'tasks': {}}
    names = {
        ('vehicles', '/vehicles'): 'vehicles',
        ('maintenance', '/maintenances'): 'maintenances',
        ('planning', '/maintenance-rules'): 'rules',
        ('planning', '/maintenance-tasks'): 'tasks',
    }

    def fake_call(service, method, path, *, data=None, params=None):
        if service == 'statistics':
            if path == '/statistics/summary':
                return {'year': None, 'vehicle_count': 1, 'maintenance_count': 0,
                        'total_cost': 0, 'average_cost': 0, 'most_expensive': None}
            raise AssertionError((service, path))
        if service == 'notifications':
            if path.endswith('/preferences'):
                return {'email_enabled': data['email_enabled'], 'reminder_offsets_days': data['reminder_offsets_days']} if data else {'email_enabled': False, 'reminder_offsets_days': [90, 30, 7, 1]}
            if path.endswith('/scan'):
                return {'created': 0, 'scanned': 0}
            if path.endswith('/test'):
                return {'message': 'Correo de prueba enviado'}
            if path.startswith('/notifications/'):
                return []
        for (candidate_service, base), kind in names.items():
            if service != candidate_service or not (path == base or path.startswith(base + '/')):
                continue
            table = state[kind]
            suffix = path[len(base):].strip('/')
            key = int(suffix) if suffix.isdigit() else None
            if method == 'GET':
                if key is None:
                    return copy.deepcopy(list(table.values()))
                return copy.deepcopy(table[key])
            if method == 'POST' and key is None:
                new_id = max(table, default=0) + 1
                row = {'id': new_id, **copy.deepcopy(data)}
                if kind == 'tasks':
                    row.update({'status': 'pending', 'completed_date': None, 'completed_mileage': None})
                table[new_id] = row
                return copy.deepcopy(row)
            if method == 'PUT' and key is not None:
                row = {'id': key, **copy.deepcopy(data)}
                if kind == 'tasks':
                    row.update({'status': 'pending', 'completed_date': None, 'completed_mileage': None})
                table[key] = row
                return copy.deepcopy(row)
            if method == 'DELETE' and key is not None:
                del table[key]
                return None
            if kind == 'tasks' and method == 'PATCH' and suffix.endswith('/complete'):
                task_id = int(suffix.split('/')[0])
                table[task_id].update({'status': 'completed', **data})
                return copy.deepcopy(table[task_id])
        raise AssertionError((service, method, path, data, params))

    monkeypatch.setattr(resources, 'call', fake_call)
    monkeypatch.setattr(insights, 'call', fake_call)
    try:
        with TestClient(app) as client:
            reg = client.post('/api/auth/register', json={'full_name': 'Prueba Swagger',
                         'email': 'swagger@example.org', 'password': 'anexamplepassword'})
            assert reg.status_code == 201, reg.text
            auth = {'Authorization': 'Bearer ' + reg.json()['token']}

            vehicle = {'brand': 'Seat', 'model': 'Ibiza', 'year': 2021, 'current_mileage': 62000}
            car = client.post('/api/vehicles', json=vehicle, headers=auth)
            assert car.status_code == 201, car.text
            vehicle_id = car.json()['id']
            assert len(client.get('/api/vehicles', headers=auth).json()) == 1
            assert client.get(f'/api/vehicles/{vehicle_id}', headers=auth).status_code == 200
            car = client.put(f'/api/vehicles/{vehicle_id}', json={**vehicle, 'current_mileage': 64000}, headers=auth)
            assert car.status_code == 200 and car.json()['current_mileage'] == 64000

            maint = {'vehicle_id': vehicle_id, 'maintenance_type': 'oil_change',
                     'date': '2026-11-21', 'mileage': 64000,
                     'description': 'Cambio de aceite', 'cost': 89.90}
            m = client.post('/api/maintenances', json=maint, headers=auth)
            assert m.status_code == 201, m.text
            mid = m.json()['id']
            assert len(client.get('/api/maintenances', headers=auth).json()) == 1
            assert client.get(f'/api/maintenances/{mid}', headers=auth).status_code == 200
            assert client.put(f'/api/maintenances/{mid}', json={**maint, 'cost': 95.0}, headers=auth).status_code == 200

            rule = {'vehicle_id': vehicle_id, 'name': 'Aceite anual', 'maintenance_type': 'oil_change',
                    'interval_months': 12, 'last_performed_date': '2026-11-21'}
            r = client.post('/api/rules', json=rule, headers=auth)
            assert r.status_code == 201, r.text
            rid = r.json()['id']
            assert client.get('/api/rules', headers=auth).status_code == 200
            assert client.get(f'/api/rules/{rid}', headers=auth).status_code == 200
            assert client.put(f'/api/rules/{rid}', json={**rule, 'name': 'Aceite cada año'}, headers=auth).status_code == 200

            task = {'vehicle_id': vehicle_id, 'rule_id': rid, 'name': 'Cambio de aceite', 'due_date': '2027-11-21'}
            t = client.post('/api/tasks', json=task, headers=auth)
            assert t.status_code == 201, t.text
            tid = t.json()['id']
            assert client.get('/api/tasks', headers=auth).status_code == 200
            assert client.get('/api/tasks?status=pending', headers=auth).status_code == 200
            assert client.get(f'/api/tasks/{tid}', headers=auth).status_code == 200
            assert client.put(f'/api/tasks/{tid}', json=task, headers=auth).status_code == 200
            complete = client.patch(f'/api/tasks/{tid}/complete',
                                    json={'completed_date': '2026-11-22', 'completed_mileage': 65000}, headers=auth)
            assert complete.status_code == 200, complete.text
            assert complete.json()['status'] == 'completed'

            assert client.get('/api/statistics/summary', headers=auth).status_code == 200
            assert client.get('/api/notifications/preferences', headers=auth).status_code == 200
            assert client.put('/api/notifications/preferences', headers=auth,
                              json={'email_enabled': False, 'reminder_offsets_days': [30, 7]}).status_code == 200
            assert client.post('/api/notifications/scan', headers=auth).status_code == 200

            assert client.delete(f'/api/tasks/{tid}', headers=auth).status_code == 204
            assert client.delete(f'/api/rules/{rid}', headers=auth).status_code == 204
            assert client.delete(f'/api/maintenances/{mid}', headers=auth).status_code == 204
            assert client.delete(f'/api/vehicles/{vehicle_id}', headers=auth).status_code == 204
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
