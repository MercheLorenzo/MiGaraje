from datetime import date,timedelta
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import Base
from app.models.notification import Notification,Preference
from app.services.notification_service import scan

def test_scan_deduplicates():
    engine=create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        task={"id":20,"vehicle_id":5,"name":"ITV","status":"pending","due_date":(date.today()+timedelta(days=4)).isoformat(),"due_mileage":None}
        vehicle={"id":5,"current_mileage":1500}
        assert scan(db,1,[5],"test@example.com",all_tasks=[task],all_vehicles=[vehicle])["created"]==1
        assert scan(db,1,[5],"test@example.com",all_tasks=[task],all_vehicles=[vehicle])["created"]==0



def test_cleanup_vehicle_and_task_notifications(monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.main import app
    from app.db.session import get_db

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with factory() as db:
            for user, vehicle, task in [(1, 5, 10), (1, 5, 11), (1, 6, 12), (2, 5, 10)]:
                db.add(Notification(
                    user_id=user, vehicle_id=vehicle, task_id=task,
                    dedupe_key=f"{user}-{vehicle}-{task}", title="Revisión",
                    body="Mantenimiento pendiente", level="warning",
                    email_status="disabled",
                ))
            db.commit()

        with TestClient(app) as client:
            assert client.delete("/notifications/1/task/10").status_code == 204
            assert {n["task_id"] for n in client.get("/notifications/1").json()} == {11, 12}
            assert client.delete("/notifications/1/vehicle/5").status_code == 204
            assert [n["task_id"] for n in client.get("/notifications/1").json()] == [12]
            assert [n["task_id"] for n in client.get("/notifications/2").json()] == [10]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
