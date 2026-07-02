from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
import hashlib
import secrets

class Utilisateur(Base):
    __tablename__ = 'utilisateurs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    mot_de_passe_hash = Column(String(256), nullable=False)
    sel = Column(String(64), nullable=False)
    organisation = Column(String(200))
    role = Column(String(50), default='chercheur')  # chercheur, admin
    actif = Column(Boolean, default=True)
    date_inscription = Column(DateTime, default=datetime.utcnow)
    derniere_connexion = Column(DateTime)

    @staticmethod
    def hacher_mot_de_passe(mot_de_passe: str, sel: str = None) -> tuple:
        """Hache le mot de passe avec un sel"""
        if sel is None:
            sel = secrets.token_hex(32)
        hash_obj = hashlib.pbkdf2_hmac('sha256', mot_de_passe.encode(), sel.encode(), 100000)
        return hash_obj.hex(), sel

    def verifier_mot_de_passe(self, mot_de_passe: str) -> bool:
        """Vérifie le mot de passe"""
        hash_entre, _ = self.hacher_mot_de_passe(mot_de_passe, self.sel)
        return hash_entre == self.mot_de_passe_hash

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'organisation': self.organisation,
            'role': self.role,
            'date_inscription': str(self.date_inscription)
        }
