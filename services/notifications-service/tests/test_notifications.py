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
