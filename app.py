from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Utilisateur
from auth import creer_token, decoder_token
import hashlib
import secrets
class UtilisateurInscription(BaseModel):
    nom: str
    email: str
    mot_de_passe: str
    organisation: Optional[str] = None

class UtilisateurConnexion(BaseModel):
    email: str
    mot_de_passe: str

class UtilisateurResponse(BaseModel):
    id: int
    nom: str
    email: str
    organisation: Optional[str] = None
    role: str
    token: str
    security = HTTPBearer()

async def get_utilisateur_courant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Récupère l'utilisateur à partir du token JWT"""
    token = credentials.credentials
    payload = decoder_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    
    utilisateur = db.query(Utilisateur).filter(Utilisateur.id == payload['sub']).first()
    if not utilisateur or not utilisateur.actif:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return utilisateur
    # ==================== AUTHENTIFICATION ====================

@app.post("/auth/inscription", response_model=UtilisateurResponse)
async def inscription(user: UtilisateurInscription, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur"""
    
    # Vérifier si l'email existe déjà
    existant = db.query(Utilisateur).filter(Utilisateur.email == user.email).first()
    if existant:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    # Hacher le mot de passe
    hash_mdp, sel = Utilisateur.hacher_mot_de_passe(user.mot_de_passe)
    
    nouvel_utilisateur = Utilisateur(
        nom=user.nom,
        email=user.email,
        mot_de_passe_hash=hash_mdp,
        sel=sel,
        organisation=user.organisation,
        role='chercheur'
    )
    
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    
    # Créer le token
    token = creer_token(nouvel_utilisateur.id, nouvel_utilisateur.email)
    
    return UtilisateurResponse(
        id=nouvel_utilisateur.id,
        nom=nouvel_utilisateur.nom,
        email=nouvel_utilisateur.email,
        organisation=nouvel_utilisateur.organisation,
        role=nouvel_utilisateur.role,
        token=token
    )

@app.post("/auth/connexion", response_model=UtilisateurResponse)
async def connexion(user: UtilisateurConnexion, db: Session = Depends(get_db)):
    """Connexion d'un utilisateur"""
    
    utilisateur = db.query(Utilisateur).filter(Utilisateur.email == user.email).first()
    
    if not utilisateur or not utilisateur.verifier_mot_de_passe(user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    if not utilisateur.actif:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    
    # Mettre à jour la date de dernière connexion
    utilisateur.derniere_connexion = datetime.utcnow()
    db.commit()
    
    # Créer le token
    token = creer_token(utilisateur.id, utilisateur.email)
    
    return UtilisateurResponse(
        id=utilisateur.id,
        nom=utilisateur.nom,
        email=utilisateur.email,
        organisation=utilisateur.organisation,
        role=utilisateur.role,
        token=token
    )

@app.get("/auth/profil")
async def profil(utilisateur: Utilisateur = Depends(get_utilisateur_courant)):
    """Récupère le profil de l'utilisateur connecté"""
    return utilisateur.to_dict()
