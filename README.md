# Gestion d'une Bibliotheque

Application web academique avec **Flask + SQLite + HTML/CSS** pour la gestion d'une bibliotheque universitaire.
Le projet relie la modelisation UML (cas d'utilisation, classes, sequences) a une implementation complete en Python.

## Objectifs
- Gerer les ouvrages, les usagers, les emprunts, retours et reservations.
- Fournir une interface `admin` et une interface `usager`.
- Montrer la transition UML -> application fonctionnelle.

## Fonctionnalites principales
- Catalogue public consultable sans compte.
- Inscription / connexion usager.
- Demandes d'emprunt et reservations (compte requis).
- Validation/rejet des demandes par l'administrateur.
- Gestion des retours et historique des emprunts.
- Suspension automatique (retards) et manuelle des usagers.
- Dashboard admin et dashboard usager avec indicateurs + graphiques.

## Comptes
- Admin par defaut :
  - Email : `admin@bibliotheque.local`
  - Mot de passe : `admin1234`

## Stack
- Backend : Python / Flask
- Frontend : HTML, CSS, Jinja2
- Base de donnees : SQLite (`library.db`)
- UML : fichiers PlantUML dans `diagrams/`

## Structure
- `app.py` : routes Flask, regles metier, init DB
- `templates/` : interfaces Jinja2
- `static/style.css` : design system et responsive UI
- `library.db` : base SQLite locale
- `diagrams/` : diagrammes UML du projet

## Installation
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
```

## Lancement
```bash
python app.py
```
Puis ouvrir `http://127.0.0.1:5000`.

## Notes
- La base est creee/migree automatiquement au lancement.
- Les actions d'emprunt/reservation necessitent une session usager.
- Les visiteurs non connectes peuvent parcourir tout le catalogue.
