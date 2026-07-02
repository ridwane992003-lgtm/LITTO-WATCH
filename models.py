from sqlalchemy import Column, Integer, Float, String, Text, Date, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from datetime import datetime
import os

Base = declarative_base()

# Modèle Observation
class Observation(Base):
    __tablename__ = 'observations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', 4326))
    date = Column(Date, nullable=False)
    
    # Paramètres abiotiques
    temperature_eau = Column(Float)
    salinite = Column(Float)
    ph = Column(Float)
    oxygene_dissous = Column(Float)
    turbidite = Column(Float)
    conductivite = Column(Float)
    profondeur = Column(Float)
    
    # Nutriments
    nitrates = Column(Float)
    phosphates = Column(Float)
    matiere_organique = Column(Float)
    
    # Habitat
    type_mangrove = Column(String(100))
    nature_sol = Column(String(100))
    niveau_degradation = Column(String(50))
    
    # Biodiversité
    especes_presentes = Column(Text)
    
    # Notes terrain
    notes = Column(Text)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'date': str(self.date),
            'temperature_eau': self.temperature_eau,
            'salinite': self.salinite,
            'ph': self.ph,
            'oxygene_dissous': self.oxygene_dissous,
            'turbidite': self.turbidite,
            'conductivite': self.conductivite,
            'profondeur': self.profondeur,
            'nitrates': self.nitrates,
            'phosphates': self.phosphates,
            'matiere_organique': self.matiere_organique,
            'type_mangrove': self.type_mangrove,
            'nature_sol': self.nature_sol,
            'niveau_degradation': self.niveau_degradation,
            'especes_presentes': self.especes_presentes,
            'notes': self.notes,
            'created_at': str(self.created_at)
        }


# Modèle Campagne de terrain
class Campagne(Base):
    __tablename__ = 'campagnes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(200), nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date)
    description = Column(Text)
    equipe = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'date_debut': str(self.date_debut),
            'date_fin': str(self.date_fin) if self.date_fin else None,
            'description': self.description,
            'equipe': self.equipe
        }


# Modèle Alerte
class Alerte(Base):
    __tablename__ = 'alertes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_id = Column(Integer)
    parametre = Column(String(50), nullable=False)
    valeur = Column(Float, nullable=False)
    seuil_min = Column(Float)
    seuil_max = Column(Float)
    message = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'observation_id': self.observation_id,
            'parametre': self.parametre,
            'valeur': self.valeur,
            'seuil': f"[{self.seuil_min}, {self.seuil_max}]",
            'message': self.message,
            'date': str(self.date)
        }


# Modèle Espèce
class Espece(Base):
    __tablename__ = 'especes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_scientifique = Column(String(200), nullable=False, unique=True)
    nom_commun = Column(String(200))
    categorie = Column(String(50))  # Manglier, Poisson, Crustacé, Mollusque, Oiseau, Mammifère, Reptile
    statut_conservation = Column(String(50))  # LC, NT, VU, EN, CR
    description = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom_scientifique': self.nom_scientifique,
            'nom_commun': self.nom_commun,
            'categorie': self.categorie,
            'statut_conservation': self.statut_conservation,
            'description': self.description
        }


# Modèle Photo
class Photo(Base):
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_id = Column(Integer)
    url = Column(String(500), nullable=False)
    legende = Column(String(300))
    date_prise = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'observation_id': self.observation_id,
            'url': self.url,
            'legende': self.legende,
            'date_prise': str(self.date_prise) if self.date_prise else None
        }


# Configuration de la base de données
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/litto_watch'
)

# Remplacer postgres:// par postgresql:// si nécessaire (Render)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Créer toutes les tables dans la base de données"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
