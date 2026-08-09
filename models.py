from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from datetime import datetime, timezone
from database import Base

class LabReading(Base):
    __tablename__ = "lab_readings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Session & Timing metadata
    session_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Raw Sensor Values
    ph = Column(Float, nullable=False)
    tds = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    nh3 = Column(Float, nullable=False)

    # Kinetic Metrics (Day 5 requirements)
    tds_stable_time = Column(Float, nullable=True)
    nh3_slope = Column(Float, nullable=True)

    # Decision Tree Outputs from M1 (Day 3 requirements)
    status = Column(String(30), nullable=True)     # e.g., "PURE", "ADULTERATED"
    reason = Column(Text, nullable=True)           # e.g., "pH below threshold"
    confidence = Column(Float, nullable=True)      # e.g., 0.95

    # Contextual Field (Day 7 requirement)
    concentration = Column(String(50), nullable=True) # e.g., "5% Urea"
