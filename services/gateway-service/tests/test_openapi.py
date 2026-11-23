"""Tests for public Swagger coverage and the documented bearer authentication."""
from fastapi.testclient import TestClient
from app.main import app


EXPECTED = {
    '/api/auth/register': {'post'},
    '/api/auth/login': {'post'},
    '/api/auth/me': {'get', 'put'},
    '/api/auth/change-password': {'post'},
    '/api/vehicles': {'get', 'post'},
    '/api/vehicles/{vehicle_id}': {'get', 'put', 'delete'},
    '/api/maintenances': {'get', 'post'},
    '/api/maintenances/{record_id}': {'get', 'put', 'delete'},
    '/api/rules': {'get', 'post'},
    '/api/rules/{record_id}': {'get', 'put', 'delete'},
    '/api/rules/{rule_id}/generate': {'post'},
    '/api/tasks': {'get', 'post'},
    '/api/tasks/{record_id}': {'get', 'put', 'delete'},
    '/api/tasks/{task_id}/complete': {'patch'},
    '/api/statistics/summary': {'get'},
    '/api/statistics/monthly': {'get'},
    '/api/statistics/categories': {'get'},
    '/api/statistics/comparison': {'get'},
    '/api/statistics/vehicles/{vehicle_id}': {'get'},
    '/api/notifications': {'get'},
    '/api/notifications/preferences': {'get', 'put'},
    '/api/notifications/scan': {'post'},
    '/api/notifications/{notification_id}/read': {'patch'},
    '/api/notifications/test': {'post'},
}


def test_public_openapi_routes_are_explicit():
    with TestClient(app) as client:
        response = client.get('/openapi.json')
    assert response.status_code == 200
    paths = response.json()['paths']
    for path, methods in EXPECTED.items():
        assert path in paths, path
        assert methods <= paths[path].keys(), (path, methods)
    assert '/api/{kind}' not in paths
    assert '/api/{kind}/{record_id}' not in paths
    assert '/internal/users' not in paths


def test_request_bodies_and_bearer_scheme_are_documented():
    spec = app.openapi()
    assert spec['components']['securitySchemes']['HTTPBearer']['scheme'] == 'bearer'
    for path in ('/api/vehicles', '/api/maintenances', '/api/rules', '/api/tasks'):
        operation = spec['paths'][path]['post']
        assert operation['requestBody']['required'] is True
        assert operation['security'] == [{'HTTPBearer': []}]
    assert spec['paths']['/api/auth/login']['post'].get('security') is None
    assert spec['paths']['/api/tasks']['get']['parameters']


def test_cannot_access_user_resources_without_token():
    with TestClient(app) as client:
        for path in ('/api/vehicles', '/api/maintenances', '/api/rules', '/api/tasks', '/api/statistics/summary', '/api/notifications'):
            assert client.get(path).status_code == 401
