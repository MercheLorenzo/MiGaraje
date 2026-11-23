import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import Base
from app.models.account import User, VehicleOwner
from app.services.auth import hash_password
from app.tools import claim_legacy_vehicles as tool


def test_only_claim_unowned_vehicles(monkeypatch):
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    monkeypatch.setattr(tool, 'call', lambda *args, **kwargs: [{'id': 1}, {'id': 2}])
    with Session(engine) as db:
        user = User(email='example@example.com', full_name='Persona Ejemplo', password_hash=hash_password('somepasswordabcdef'))
        db.add(user)
        db.commit()
        assert tool.assign(db, 'example@example.com', [1]) == 1
        assert db.query(VehicleOwner).count() == 1
        with pytest.raises(ValueError):
            tool.assign(db, 'example@example.com', [1])
        with pytest.raises(ValueError):
            tool.assign(db, 'example@example.com', [99])
