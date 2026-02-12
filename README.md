# Gestion d'une Bibliotheque - Flask

Application Flask avec authentification par role:
- `admin`: supervision globale, validation des demandes d'emprunt, cloture des retours, gestion des ouvrages/usagers/reservations.
- `user`: demandes d'emprunt, reservations, suivi de ses emprunts et de son historique.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancer l'application

```powershell
python app.py
```

Puis ouvrir `http://127.0.0.1:5000`.

## Compte admin par defaut

- Email: `admin@bibliotheque.local`
- Mot de passe: `admin1234`

Pensez a changer ce mot de passe en production.

## Donnees

La base SQLite (`library.db`) est creee automatiquement au premier lancement.
