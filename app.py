from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    Observation, Alerte, Campagne, Espece, Photo,
    init_db, get_db, SessionLocal
)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import os

app = FastAPI(title="LITTO-WATCH API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour validation
class ObservationCreate(BaseModel):
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

class CampagneCreate(BaseModel):
    nom: str
    date_debut: str
    date_fin: Optional[str] = None
    description: Optional[str] = None
    equipe: Optional[str] = None

class EspeceCreate(BaseModel):
    nom_scientifique: str
    nom_commun: Optional[str] = None
    categorie: Optional[str] = None
    statut_conservation: Optional[str] = None
    description: Optional[str] = None

# Seuils d'alerte
SEUILS = {
    "temperature_eau": (15, 35),
    "salinite": (5, 45),
    "ph": (6.5, 8.5),
    "oxygene_dissous": (2, 10),
    "turbidite": (0, 50),
}

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {
        "plateforme": "LITTO-WATCH",
        "version": "1.0.0",
        "endpoints": [
            "/observations",
            "/campagnes",
            "/especes",
            "/alertes",
            "/stats",
            "/export/csv",
            "/export/excel",
            "/upload/csv",
            "/upload/excel"
        ]
    }

# ==================== OBSERVATIONS ====================

@app.post("/observations")
async def add_observation(obs: ObservationCreate, db: Session = Depends(get_db)):
    try:
        db_obs = Observation(
            latitude=obs.latitude,
            longitude=obs.longitude,
            date=datetime.strptime(obs.date, "%Y-%m-%d").date(),
            temperature_eau=obs.temperature_eau,
            salinite=obs.salinite,
            ph=obs.ph,
            oxygene_dissous=obs.oxygene_dissous,
            turbidite=obs.turbidite,
            conductivite=obs.conductivite,
            profondeur=obs.profondeur,
            nitrates=obs.nitrates,
            phosphates=obs.phosphates,
            matiere_organique=obs.matiere_organique,
            type_mangrove=obs.type_mangrove,
            nature_sol=obs.nature_sol,
            niveau_degradation=obs.niveau_degradation,
            especes_presentes=obs.especes_presentes,
            notes=obs.notes
        )
        # Mise à jour de la géométrie PostGIS
        db_obs.geom = func.ST_SetSRID(
            func.ST_MakePoint(obs.longitude, obs.latitude), 4326
        )
        
        db.add(db_obs)
        db.commit()
        db.refresh(db_obs)
        
        # Vérification des alertes
        check_alerts(db_obs, db)
        
        return {"status": "succès", "id": db_obs.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/observations")
async def get_observations(db: Session = Depends(get_db)):
    observations = db.query(Observation).order_by(Observation.date.desc()).all()
    return [obs.to_dict() for obs in observations]

@app.get("/observations/{obs_id}")
async def get_observation(obs_id: int, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation non trouvée")
    return obs.to_dict()

# ==================== CAMPAGNES ====================

@app.post("/campagnes")
async def create_campagne(campagne: CampagneCreate, db: Session = Depends(get_db)):
    try:
        db_campagne = Campagne(
            nom=campagne.nom,
            date_debut=datetime.strptime(campagne.date_debut, "%Y-%m-%d").date(),
            date_fin=datetime.strptime(campagne.date_fin, "%Y-%m-%d").date() if campagne.date_fin else None,
            description=campagne.description,
            equipe=campagne.equipe
        )
        db.add(db_campagne)
        db.commit()
        db.refresh(db_campagne)
        return {"status": "succès", "id": db_campagne.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campagnes")
async def get_campagnes(db: Session = Depends(get_db)):
    campagnes = db.query(Campagne).all()
    return [c.to_dict() for c in campagnes]

# ==================== ESPÈCES ====================

@app.post("/especes")
async def add_espece(espece: EspeceCreate, db: Session = Depends(get_db)):
    try:
        db_espece = Espece(**espece.dict())
        db.add(db_espece)
        db.commit()
        return {"status": "succès", "id": db_espece.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/especes")
async def get_especes(categorie: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Espece)
    if categorie:
        query = query.filter(Espece.categorie == categorie)
    especes = query.all()
    return [e.to_dict() for e in especes]

# ==================== ALERTES ====================

@app.get("/alertes")
async def get_alertes(db: Session = Depends(get_db)):
    alertes = db.query(Alerte).order_by(Alerte.created_at.desc()).limit(50).all()
    return [a.to_dict() for a in alertes]

def check_alerts(obs: Observation, db: Session):
    """Vérifie les dépassements de seuils et crée des alertes"""
    for param, (min_val, max_val) in SEUILS.items():
        valeur = getattr(obs, param, None)
        if valeur is not None and (valeur < min_val or valeur > max_val):
            alerte = Alerte(
                observation_id=obs.id,
                parametre=param,
                valeur=valeur,
                seuil_min=min_val,
                seuil_max=max_val,
                message=f"Alerte: {param} = {valeur} (seuil: [{min_val}, {max_val}])",
                date=obs.date
            )
            db.add(alerte)
    db.commit()

# ==================== STATISTIQUES ====================

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    observations = db.query(Observation).all()
    
    if not observations:
        return {"message": "Aucune donnée disponible"}
    
    nb = len(observations)
    temp_values = [o.temperature_eau for o in observations if o.temperature_eau]
    salinite_values = [o.salinite for o in observations if o.salinite]
    ph_values = [o.ph for o in observations if o.ph]
    
    return {
        "nombre_observations": nb,
        "temperature_moyenne": sum(temp_values)/len(temp_values) if temp_values else None,
        "salinite_moyenne": sum(salinite_values)/len(salinite_values) if salinite_values else None,
        "ph_moyen": sum(ph_values)/len(ph_values) if ph_values else None,
        "niveau_degradation": db.query(
            Observation.niveau_degradation,
            func.count(Observation.niveau_degradation)
        ).group_by(Observation.niveau_degradation).all(),
        "type_mangrove": db.query(
            Observation.type_mangrove,
            func.count(Observation.type_mangrove)
        ).group_by(Observation.type_mangrove).all()
    }

# ==================== IMPORT/EXPORT ====================

@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_csv(file.file)
        observations_added = 0
        
        for _, row in df.iterrows():
            obs = Observation(
                latitude=row.get('latitude'),
                longitude=row.get('longitude'),
                date=pd.to_datetime(row.get('date')).date(),
                temperature_eau=row.get('temperature_eau'),
                salinite=row.get('salinite'),
                ph=row.get('ph'),
                oxygene_dissous=row.get('oxygene_dissous'),
                turbidite=row.get('turbidite'),
                conductivite=row.get('conductivite'),
                profondeur=row.get('profondeur'),
                nitrates=row.get('nitrates'),
                phosphates=row.get('phosphates'),
                matiere_organique=row.get('matiere_organique'),
                type_mangrove=row.get('type_mangrove'),
                nature_sol=row.get('nature_sol'),
                niveau_degradation=row.get('niveau_degradation'),
                especes_presentes=row.get('especes_presentes'),
                notes=row.get('notes')
            )
            obs.geom = func.ST_SetSRID(
                func.ST_MakePoint(obs.longitude, obs.latitude), 4326
            )
            db.add(obs)
            observations_added += 1
        
        db.commit()
        return {"status": "succès", "lignes_importées": observations_added}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    observations = db.query(Observation).all()
    if not observations:
        raise HTTPException(status_code=404, detail="Aucune donnée")
    
    data = [obs.to_dict() for obs in observations]
    df = pd.DataFrame(data)
    return {"data": df.to_csv(index=False)}

# ==================== LANCEMENT ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
