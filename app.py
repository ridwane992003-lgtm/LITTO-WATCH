from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
import os

app = FastAPI(title="LITTO-WATCH API", version="1.0.0")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données
class FieldObservation(BaseModel):
    latitude: float
    longitude: float
    date: str
    temperature_eau: Optional[float] = None
    salinite: Optional[float] = None
    ph: Optional[float] = None
    oxygene_dissous: Optional[float] = None
    turbidite: Optional[float] = None
    conductivite: Optional[float] = None
    profondeur: Optional[float] = None
    nitrates: Optional[float] = None
    phosphates: Optional[float] = None
    matiere_organique: Optional[float] = None
    type_mangrove: Optional[str] = None
    nature_sol: Optional[str] = None
    niveau_degradation: Optional[str] = None
    especes_presentes: Optional[str] = None
    notes: Optional[str] = None

class Alert(BaseModel):
    parametre: str
    valeur: float
    seuil: float
    message: str
    date: str

# Stockage en mémoire (remplacer par PostgreSQL)
observations_db = []
alerts_db = []

@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur LITTO-WATCH API",
        "version": "1.0.0",
        "endpoints": [
            "/observations",
            "/alerts",
            "/stats",
            "/export/csv",
            "/export/excel"
        ]
    }

@app.post("/observations")
async def add_observation(obs: FieldObservation):
    observations_db.append(obs.dict())
    check_alerts(obs)
    return {"status": "succès", "id": len(observations_db)}

@app.get("/observations")
async def get_observations():
    return observations_db

@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        observations_db.extend(df.to_dict('records'))
        return {"status": "succès", "lignes_importées": len(df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)
        observations_db.extend(df.to_dict('records'))
        return {"status": "succès", "lignes_importées": len(df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/export/csv")
async def export_csv():
    if not observations_db:
        raise HTTPException(status_code=404, detail="Aucune donnée")
    df = pd.DataFrame(observations_db)
    return {"data": df.to_csv(index=False)}

@app.get("/stats")
async def get_stats():
    if not observations_db:
        return {"message": "Aucune donnée disponible"}
    df = pd.DataFrame(observations_db)
    stats = {
        "nombre_observations": len(df),
        "temperature_moyenne": df['temperature_eau'].mean() if 'temperature_eau' in df.columns else None,
        "salinite_moyenne": df['salinite'].mean() if 'salinite' in df.columns else None,
        "ph_moyen": df['ph'].mean() if 'ph' in df.columns else None,
    }
    return stats

@app.get("/alerts")
async def get_alerts():
    return alerts_db

# Seuils d'alerte configurables
SEUILS = {
    "temperature_eau": (15, 35),
    "salinite": (5, 45),
    "ph": (6.5, 8.5),
    "oxygene_dissous": (2, 10),
}

def check_alerts(obs: FieldObservation):
    for param, (min_val, max_val) in SEUILS.items():
        valeur = getattr(obs, param, None)
        if valeur is not None:
            if valeur < min_val or valeur > max_val:
                alert = Alert(
                    parametre=param,
                    valeur=valeur,
                    seuil=f"[{min_val}, {max_val}]",
                    message=f"Alerte: {param} hors seuil ({valeur})",
                    date=obs.date
                )
                alerts_db.append(alert.dict())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
