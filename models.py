from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from database import Base

class LabReading(Base):
    __tablename__ = "lab_readings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)                          # Index for fast session lookup
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True) # Index for chronological sorting
    ph = Column(Float)
    tds = Column(Float)
    temperature = Column(Float)
    nh3 = Column(Float)
    tds_stable_time = Column(Float, nullable=True)
    nh3_slope = Column(Float, nullable=True)
    concentration = Column(String, nullable=True)                    # Ground truth/sample label (e.g., "5% Salt", "Pure Milk")
    
    # Classification outputs
    status = Column(String, index=True)                              # Index for status filtering (PURE / ADULTERATED)
    reason = Column(String)
    confidence = Column(Float)