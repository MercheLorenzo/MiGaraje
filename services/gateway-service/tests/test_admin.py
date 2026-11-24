"""RBAC, lectura global, filtros y ausencia de modificación cruzada."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models.account import User, VehicleOwner
from app.services.auth import create_token, hash_password
from app.services import admin_reports
from app.api.routes import resources

engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
Sessions = sessionmaker(bind=engine, expire_on_commit=False)


def override_db():
    with Sessions() as db:
        yield db


@pytest.fixture
def setup(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_db
    with Sessions() as db:
        a = User(email='admin@example.org', full_name='Admin Demo', role='admin', password_hash=hash_password('superstrong1234'))
        u = User(email='user@example.org', full_name='Persona Demo', password_hash=hash_password('superstrong4567'))
        db.add_all([a, u]); db.commit()
        db.refresh(a); db.refresh(u)
        aid, uid = a.id, u.id
        db.add_all([VehicleOwner(vehicle_id=1,user_id=uid), VehicleOwner(vehicle_id=2,user_id=aid)]);db.commit()

    vehicles = [
        {'id':1,'brand':'Seat','model':'Ibiza','year':2022,'current_mileage':21000,'license_plate':'1234AAA'},
        {'id':2,'brand':'Hyundai','model':'i20','year':2019,'current_mileage':30000,'license_plate':'5678BBB'},
        {'id':3,'brand':'Honda','model':'Civic','year':2018,'current_mileage':90000,'license_plate':'9999CCC'},
    ]
    records = [
        {'id':10,'vehicle_id':1,'maintenance_type':'oil_change','date':'2026-11-20','description':'Aceite','mileage':20000,'cost':100.5},
        {'id':11,'vehicle_id':2,'maintenance_type':'inspection','date':'2026-01-11','description':'ITV','mileage':20000,'cost':45},
        {'id':12,'vehicle_id':3,'maintenance_type':'repair','date':'2025-02-12','description':'Otros','mileage':80000,'cost':200},
    ]
    def fake_call(service, method, path, **kwargs):
        if service=='vehicles' and method=='GET' and path=='/vehicles': return vehicles
        if service=='maintenance' and method=='GET' and path=='/maintenances': return records
        raise AssertionError((service,method,path,kwargs))
    monkeypatch.setattr(admin_reports,'call',fake_call)
    monkeypatch.setattr(resources,'call',fake_call)
    with TestClient(app) as c:
        yield c,{'Authorization':'Bearer '+create_token(aid)},{'Authorization':'Bearer '+create_token(uid)}
    app.dependency_overrides.clear()


def test_roles_and_read_only_admin_routes(setup):
    client, admin, user=setup
    assert client.get('/api/admin/overview').status_code==401
    for route in ['/api/admin/overview','/api/admin/users','/api/admin/vehicles','/api/admin/maintenances']:
        assert client.get(route,headers=user).status_code==403
        assert client.get(route,headers=admin).status_code==200
    assert client.post('/api/admin/vehicles',headers=admin,json={}).status_code==405
    assert client.delete('/api/admin/vehicles/1',headers=admin).status_code==404
    assert client.get('/api/auth/me',headers=admin).json()['role']=='admin'
    assert client.get('/api/auth/me',headers=user).json()['role']=='user'
    assert 'password_hash' not in str(client.get('/api/admin/users',headers=admin).json())


def test_global_counts_and_period(setup):
    client,admin,_=setup
    result=client.get('/api/admin/overview',headers=admin).json()
    assert (result['user_count'],result['vehicle_count'],result['maintenance_count'])==(2,3,3)
    assert result['unassigned_vehicle_count']==1
    assert result['total_cost']==345.5
    current=client.get('/api/admin/overview?year=2026',headers=admin).json()
    assert (current['maintenance_count'],current['total_cost'])==(2,145.5)
    assert sum(c['total'] for c in current['categories'])==145.5
    assert sum(m['count'] for m in current['monthly'])==2
    assert client.get('/api/admin/overview?year=1800',headers=admin).status_code==422


def test_filters_and_no_cross_user_permissions(setup):
    client,admin,user=setup
    users=client.get('/api/admin/users',headers=admin).json()
    assert len(users)==2
    assert next(u for u in users if u['role']=='user')['total_cost']==100.5
    vehicles=client.get('/api/admin/vehicles',headers=admin).json()
    assert len(vehicles)==3
    assert [v['id'] for v in client.get('/api/admin/vehicles?user_id=2',headers=admin).json()]==[1]
    assert [r['id'] for r in client.get('/api/admin/maintenances?vehicle_id=2',headers=admin).json()]==[11]
    assert [r['id'] for r in client.get('/api/admin/maintenances?user_id=2&year=2026',headers=admin).json()]==[10]
    assert [v['id'] for v in client.get('/api/vehicles',headers=user).json()]==[1]
    # Incluso siendo admin, las rutas CRUD ordinarias siguen aisladas por propietario.
    assert client.get('/api/vehicles/1',headers=admin).status_code==404


def test_public_registration_cannot_choose_admin_role(setup):
    client,_,_=setup
    result=client.post('/api/auth/register',json={
        'email':'new@example.org','full_name':'Nueva Persona','password':'testpassword2026','role':'admin'
    })
    assert result.status_code==201
    assert result.json()['user']['role']=='user'
