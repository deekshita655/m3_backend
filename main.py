from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for M4's frontend (Streamlit / React / Browser apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Root & Health Check ---
@app.get("/")
def home():
    return {"message": "M3 Backend API is live!", "status": "ok"}

@app.get("/ping")
def ping():
    return {"status": "ok"}


# --- POST /api/readings ---
@app.post(
    "/api/readings", 
    response_model=schemas.LabReadingResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_reading(
    payload: schemas.LabReadingCreate, 
    db: Session = Depends(database.get_db)
):
    data_dict = payload.model_dump()
    
    classification_result = classifier.classify(
        ph=payload.ph,
        tds=payload.tds,
        nh3=payload.nh3,
        tds_stable=payload.tds_stable_time,
        nh3_slope=payload.nh3_slope
    )
    
    data_dict["status"] = classification_result["status"]
    data_dict["reason"] = classification_result["reason"]
    data_dict["confidence"] = classification_result["confidence"]
    
    db_reading = models.LabReading(**data_dict)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    return db_reading


# --- GET /api/readings/latest ---
@app.get("/api/readings/latest", response_model=schemas.LabReadingResponse)
def get_latest_reading(db: Session = Depends(database.get_db)):
    reading = db.query(models.LabReading).order_by(models.LabReading.id.desc()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No lab readings found")
    return reading


# --- GET /api/history ---
@app.get("/api/history", response_model=List[schemas.LabReadingResponse])
def get_history(
    status_filter: Optional[str] = Query(None, description="Filter by status: PURE, ADULTERATED, SPOILED"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    query = db.query(models.LabReading)
    
    if status_filter:
        query = query.filter(models.LabReading.status == status_filter.upper())
        
    readings = query.order_by(models.LabReading.id.desc()).offset(skip).limit(limit).all()
    return readings


# --- GET /api/stats ---
@app.get("/api/stats")
def get_summary_stats(db: Session = Depends(database.get_db)):
    total_tests = db.query(models.LabReading).count()
    if total_tests == 0:
        return {
            "total_tests": 0,
            "pure_count": 0,
            "adulterated_count": 0,
            "spoiled_count": 0,
            "avg_tds_stable_time_sec": 0.0,
            "avg_nh3_slope": 0.0
        }

    pure_count = db.query(models.LabReading).filter(models.LabReading.status == "PURE").count()
    adulterated_count = db.query(models.LabReading).filter(models.LabReading.status == "ADULTERATED").count()
    spoiled_count = db.query(models.LabReading).filter(models.LabReading.status == "SPOILED").count()

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


# --- Day 6 Updated: GET /api/accuracy ---
@app.get("/api/accuracy")
def get_model_accuracy(db: Session = Depends(database.get_db)):
    """
    Calculates overall classification accuracy and confusion metrics 
    by comparing predicted status against concentration ground truth.
    """
    all_readings = db.query(models.LabReading).all()
    if not all_readings:
        return {
            "total_evaluated": 0,
            "accuracy_pct": 0.0,
            "correct_predictions": 0,
            "incorrect_predictions": 0
        }

    correct_predictions = 0
    total_evaluated = 0

    for reading in all_readings:
        # Safe fallback if concentration is None
        conc = (reading.concentration or "").lower()
        
        # Safe fallback if status is None
        predicted_status = (reading.status or "").upper()

        # Skip rows that don't have a valid classification status
        if not predicted_status:
            continue

        # Determine ground truth based on concentration label
        if "pure" in conc or conc == "":
            ground_truth = "PURE"
        else:
            ground_truth = "ADULTERATED"

        total_evaluated += 1
        if predicted_status == ground_truth:
            correct_predictions += 1

    accuracy_pct = (correct_predictions / total_evaluated) * 100 if total_evaluated > 0 else 0.0

    return {
        "total_evaluated": total_evaluated,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": total_evaluated - correct_predictions,
        "accuracy_pct": round(accuracy_pct, 2)
    }