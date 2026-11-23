import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app
from app.models.account import User, VehicleOwner
from app.api.routes import resources
from app.services.auth import hash_password, create_token

engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
Sessions = sessionmaker(bind=engine, expire_on_commit=False)

def override_db():
    with Sessions() as db:
        yield db

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_registration_login_profile_and_password_rotation(client):
    body = {'full_name': 'Persona Ejemplo', 'email': 'example@example.org', 'password': 'securepassword0123'}
    r = client.post('/api/auth/register', json=body)
    assert r.status_code == 201, r.text
    token = r.json()['token']
    assert client.post('/api/auth/register', json=body).status_code == 409
    assert client.post('/api/auth/login', json={'email': body['email'], 'password': 'nottherightone'}).status_code == 401
    assert client.get('/api/auth/me').status_code == 401
    assert client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + token}).json()['full_name'] == 'Persona Ejemplo'
    r = client.post('/api/auth/change-password', json={'current_password': body['password'], 'new_password': 'anewpassword7788'}, headers={'Authorization': 'Bearer ' + token})
    assert r.status_code == 200
    assert client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401
    assert client.post('/api/auth/login', json={'email': body['email'], 'password': 'anewpassword7788'}).status_code == 200

def test_ownership_checks_and_cross_user_access(client, monkeypatch):
    with Sessions() as db:
        a = User(email='a@example.org', full_name='Usuario A', password_hash=hash_password('passwordnumberone'))
        b = User(email='b@example.org', full_name='Usuario B', password_hash=hash_password('passwordnumbertwo'))
        db.add_all([a, b]); db.commit(); db.refresh(a); db.refresh(b)
        aid, bid = a.id, b.id
        db.add_all([VehicleOwner(vehicle_id=1, user_id=aid), VehicleOwner(vehicle_id=2, user_id=bid)]); db.commit()
    def fake_call(service, method, path, **kwargs):
        if path == '/vehicles': return [{'id': 1, 'brand': 'Seat'}, {'id': 2, 'brand': 'Toyota'}]
        if path == '/maintenances': return [{'id': 10, 'vehicle_id': 1, 'cost': 10}, {'id': 11, 'vehicle_id': 2, 'cost': 20}]
        if path == '/maintenances/11': return {'id': 11, 'vehicle_id': 2, 'cost': 20}
        if path == '/maintenance-tasks': return [{'id': 21, 'vehicle_id': 2, 'name': 'ITV'}]
        raise AssertionError((service, method, path))
    monkeypatch.setattr(resources, 'call', fake_call)
    h = {'Authorization': 'Bearer ' + create_token(aid)}
    assert [v['id'] for v in client.get('/api/vehicles', headers=h).json()] == [1]
    assert [v['id'] for v in client.get('/api/maintenances', headers=h).json()] == [10]
    assert client.get('/api/maintenances/11', headers=h).status_code == 404
    assert client.post('/api/tasks', json={'vehicle_id': 2, 'name': 'ITV'}, headers=h).status_code == 404
    assert client.get('/api/vehicles/2', headers=h).status_code == 404
    assert client.get('/internal/users').status_code == 401
