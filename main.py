from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from typing import List

import database
import models
import schemas
import classifier  # <--- Import M1's classification logic!

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="M3 Lab Backend API", version="1.0.0")

@app.get("/")
def home():
    return {"message": "M3 Backend API is live!", "status": "ok"}

@app.get("/ping")
def ping():
    return {"status": "ok"}


# --- Day 3 Updated: POST /api/readings with Auto-Classification ---
@app.post(
    "/api/readings", 
    response_model=schemas.LabReadingResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_reading(
    payload: schemas.LabReadingCreate, 
    db: Session = Depends(database.get_db)
):
    # 1. Convert payload to dictionary
    data_dict = payload.model_dump()
    
    # 2. Run M1's Decision Tree Classifier automatically
    classification_result = classifier.classify(
        ph=payload.ph,
        tds=payload.tds,
        nh3=payload.nh3,
        tds_stable=payload.tds_stable_time,
        nh3_slope=payload.nh3_slope
    )
    
    # 3. Attach classification outputs to data dict
    data_dict["status"] = classification_result["status"]
    data_dict["reason"] = classification_result["reason"]
    data_dict["confidence"] = classification_result["confidence"]
    
    # 4. Save everything to SQL Database
    db_reading = models.LabReading(**data_dict)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    return db_reading


# --- GET /api/history ---
@app.get("/api/history", response_model=List[schemas.LabReadingResponse])
def get_history(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    readings = db.query(models.LabReading).offset(skip).limit(limit).all()
    return readings