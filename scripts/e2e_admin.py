#!/usr/bin/env python3
"""Prueba de rol admin con PostgreSQL real en Docker: SOLO bases descartables.

Invocar en CI tras `docker compose up ...` con MIGARAJE_E2E_ALLOW_WRITES=1.
Crea y promueve una cuenta de prueba usando el comando local, nunca una API pública.
"""
import os
import subprocess
import uuid
from datetime import date
from scripts.e2e_gateway import expect


def main():
    if os.environ.get('MIGARAJE_E2E_ALLOW_WRITES') != '1':
        raise RuntimeError('Esta prueba escribe en PostgreSQL: prohibida fuera de un entorno desechable.')

    name=uuid.uuid4().hex[:10]
    password='Demostracion_Datos_2026!'
    emails=[f'ci-admin-{name}@example.com', f'ci-user-{name}@example.com']
    sessions=[]
    for i,email in enumerate(emails):
        session=expect('POST','/api/auth/register',201,body={
            'full_name':f'Prueba Admin {i}', 'email':email, 'password':password
        })
        assert session['user']['role']=='user'
        sessions.append(session)
    old_admin_token=sessions[0]['token']
    user_token=sessions[1]['token']

    # Solo quien ya puede ejecutar comandos dentro del contenedor puede promover usuarios.
    result=subprocess.run([
        'docker','compose','exec','-T','gateway-service',
        'python','-m','app.scripts.set_admin','--email',emails[0]
    ],capture_output=True,text=True,check=True)
    assert 'Rol actualizado' in result.stdout, result.stdout
    assert expect('GET','/api/auth/me',401,token=old_admin_token)
    admin_token=expect('POST','/api/auth/login',200,body={
        'email': emails[0], 'password':password
    })['token']
    assert expect('GET','/api/auth/me',200,token=admin_token)['role']=='admin'
    expect('GET','/api/admin/overview',401)
    expect('GET','/api/admin/overview',403,token=user_token)

    a=expect('POST','/api/vehicles',201,token=admin_token,body={
        'brand':'Seat','model':'Ibiza','year':2020,'current_mileage':10000,
        'license_plate':f'ADM{name[:7].upper()}'
    })
    b=expect('POST','/api/vehicles',201,token=user_token,body={
        'brand':'Hyundai','model':'i20','year':2021,'current_mileage':12000,
        'license_plate':f'USR{name[:7].upper()}'
    })
    try:
        m=expect('POST','/api/maintenances',201,token=user_token,body={
            'vehicle_id':b['id'],'maintenance_type':'oil_change',
            'date':date.today().isoformat(),'mileage':12000,
            'description':'Revisión de demostración','cost':'125.50'
        })
        assert [v['id'] for v in expect('GET','/api/vehicles',200,token=user_token)]==[b['id']]
        expect('GET',f'/api/vehicles/{b["id"]}',404,token=admin_token)
        overview=expect('GET','/api/admin/overview',200,token=admin_token)
        assert overview['vehicle_count']>=2 and overview['total_cost']>=125.5
        assert overview['maintenance_count']>=1
        users=expect('GET','/api/admin/users',200,token=admin_token)
        assert any(u['email']==emails[1] for u in users)
        assert all('password_hash' not in u for u in users)
        vehicles=expect('GET','/api/admin/vehicles',200,token=admin_token)
        own_v=next(v for v in vehicles if v['id']==b['id'])
        assert own_v['owner_email']==emails[1]
        maint=expect('GET',f'/api/admin/maintenances?vehicle_id={b["id"]}',200,token=admin_token)
        assert any(r['id']==m['id'] for r in maint)
        assert expect('GET','/api/admin/vehicles',403,token=user_token)
        expect('POST','/api/admin/vehicles',405,token=admin_token,body={})
        print('OK: rol admin, JWT anterior revocado, 403 al usuario, vista global y solo lectura')
    finally:
        expect('DELETE',f'/api/vehicles/{b["id"]}',204,token=user_token)
        expect('DELETE',f'/api/vehicles/{a["id"]}',204,token=admin_token)


if __name__=='__main__':
    main()
