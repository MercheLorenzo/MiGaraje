from decimal import Decimal
from unittest.mock import patch
from app.services import statistics_service as service

def test_summary_and_categories():
    vehicles=[{"id":1,"brand":"Seat","model":"Ibiza"},{"id":2,"brand":"Ford","model":"Focus"}]
    records=[{"vehicle_id":1,"cost":"50.25","maintenance_type":"oil","date":"2026-03-10"},{"vehicle_id":2,"cost":"200","maintenance_type":"brakes","date":"2026-01-01"}]
    with patch.object(service,"get_data",return_value=(vehicles,records)):
        assert service.summary([1])["total_cost"]==50.25
        assert service.categories([1])[0]["category"]=="oil"
        assert len(service.monthly([1],2026))==12
        assert service.summary([])["vehicle_count"]==0
