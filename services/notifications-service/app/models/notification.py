from datetime import datetime,timezone
from sqlalchemy import Boolean,DateTime,Integer,String,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.db.session import Base

class Preference(Base):
    __tablename__="notification_preferences"
    user_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email_enabled:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)
    reminder_offsets:Mapped[str]=mapped_column(String(100),default="90,30,7,1",nullable=False)
    test_sent_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)

class Notification(Base):
    __tablename__="notifications"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,index=True,nullable=False)
    task_id:Mapped[int]=mapped_column(Integer,nullable=False)
    vehicle_id:Mapped[int]=mapped_column(Integer,nullable=False)
    dedupe_key:Mapped[str]=mapped_column(String(160),unique=True,nullable=False)
    title:Mapped[str]=mapped_column(String(160),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    level:Mapped[str]=mapped_column(String(20),default="info")
    is_read:Mapped[bool]=mapped_column(Boolean,default=False)
    email_status:Mapped[str]=mapped_column(String(32),default="disabled")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
