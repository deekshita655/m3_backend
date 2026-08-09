from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

import database
import models
import schemas
import classifier

# Create database tables automatically
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="M3 Lab Backend API",
    description="Backend API for Milk Quality Adulteration Detection & Kinetic Analysis",
    version="1.0.0"
)


# --- Root & Health Check ---
@app.get("/")
def home():
    return {"message": "M3 Backend API is live!", "status": "ok"}

@app.get("/ping")
def ping():
    return {"status": "ok"}


# --- POST /api/readings (With Kinetic Data & Classification) ---
@app.post(
    "/api/readings", 
    response_model=schemas.LabReadingResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_reading(
    payload: schemas.LabReadingCreate, 
    db: Session = Depends(database.get_db)
):
    """
    Receives sensor JSON payload (including kinetic data), 
    runs M1 classification, and stores the record in SQLite.
    """
    data_dict = payload.model_dump()
    
    # Run M1's decision tree classifier on raw + kinetic parameters
    classification_result = classifier.classify(
        ph=payload.ph,
        tds=payload.tds,
        nh3=payload.nh3,
        tds_stable=payload.tds_stable_time,
        nh3_slope=payload.nh3_slope
    )
    
    # Attach classification outputs
    data_dict["status"] = classification_result["status"]
    data_dict["reason"] = classification_result["reason"]
    data_dict["confidence"] = classification_result["confidence"]
    
    db_reading = models.LabReading(**data_dict)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    return db_reading


# --- GET /api/readings/latest (For M4's Live Badge) ---
@app.get("/api/readings/latest", response_model=schemas.LabReadingResponse)
def get_latest_reading(db: Session = Depends(database.get_db)):
    """
    Fetches only the single most recent test reading.
    """
    reading = db.query(models.LabReading).order_by(models.LabReading.id.desc()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No lab readings found")
    return reading


# --- Day 5 Updated: GET /api/history (With Optional Status Filter) ---
@app.get("/api/history", response_model=List[schemas.LabReadingResponse])
def get_history(
    status_filter: Optional[str] = Query(None, description="Filter by status, e.g. PURE, ADULTERATED, SPOILED"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """
    Fetches all historical lab readings stored in the database.
    Allows filtering by status and pagination via skip/limit.
    """
    query = db.query(models.LabReading)
    
    if status_filter:
        query = query.filter(models.LabReading.status == status_filter.upper())
        
    readings = query.order_by(models.LabReading.id.desc()).offset(skip).limit(limit).all()
    return readings


# --- Day 5 New: GET /api/stats (Summary Metrics for Dashboard) ---
@app.get("/api/stats")
def get_summary_stats(db: Session = Depends(database.get_db)):
    """
    Calculates aggregate metrics over all historical lab tests for M4 dashboard cards:
    - Total tests executed
    - Count & percentage of Pure vs Adulterated vs Spoiled
    - Average kinetic stabilization parameters
    """
    total_tests = db.query(models.LabReading).count()
    if total_tests == 0:
        return {
            "total_tests": 0,
            "pure_count": 0,
            "adulterated_count": 0,
            "spoiled_count": 0,
            "avg_tds_stable_time": 0.0,
            "avg_nh3_slope": 0.0
        }

    pure_count = db.query(models.LabReading).filter(models.LabReading.status == "PURE").count()
    adulterated_count = db.query(models.LabReading).filter(models.LabReading.status == "ADULTERATED").count()
    spoiled_count = db.query(models.LabReading).filter(models.LabReading.status == "SPOILED").count()

    # Calculate average kinetic statistics
    avg_tds_stable = db.query(func.avg(models.LabReading.tds_stable_time)).scalar() or 0.0
    avg_nh3_slope = db.query(func.avg(models.LabReading.nh3_slope)).scalar() or 0.0

    return {
        "total_tests": total_tests,
        "pure_count": pure_count,
        "adulterated_count": adulterated_count,
        "spoiled_count": spoiled_count,
        "adulteration_rate_pct": round((adulterated_count / total_tests) * 100, 2),
        "avg_tds_stable_time_sec": round(avg_tds_stable, 2),
        "avg_nh3_slope": round(avg_nh3_slope, 4)
    }