from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class LabReading(Base):
    __tablename__ = "lab_readings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    # Sensor readings
    ph = Column(Float, nullable=True)
    tds = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    nh3 = Column(Float, nullable=True)

    # Additional firmware telemetry
    mq135_voltage = Column(Float, nullable=True)
    ph_simulated = Column(Boolean, nullable=True)

    # Additional analysis parameters
    tds_stable_time = Column(Float, nullable=True)
    nh3_slope = Column(Float, nullable=True)
    concentration = Column(String, nullable=True)

    # Classification outputs
    status = Column(String, index=True)
    reason = Column(String)
    confidence = Column(Float)