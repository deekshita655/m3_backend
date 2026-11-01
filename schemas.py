from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# --- Base Schema (Shared attributes) ---
class LabReadingBase(BaseModel):
    session_id: str
    ph: Optional[float] = None
    tds: Optional[float] = None
    temperature: Optional[float] = None
    nh3: Optional[float] = None
    mq135_voltage: Optional[float] = None
    ph_simulated: Optional[bool] = None
    tds_stable_time: Optional[float] = None
    nh3_slope: Optional[float] = None
    concentration: Optional[str] = None


# --- Schema for creating a reading via POST request ---
class LabReadingCreate(LabReadingBase):
  pass  # Inherits all fields from LabReadingBase


# --- Schema for returning a reading in API Responses ---
class LabReadingResponse(LabReadingBase):
  id: int
  timestamp: Optional[datetime] = None  # <-- CHANGED: Allows None fallback
  status: Optional[str] = None
  reason: Optional[str] = None
  confidence: Optional[float] = None

  class Config:
    from_attributes = (
        True  # Allows Pydantic to convert SQLAlchemy objects automatically
    )