# Gestion d'une Bibliotheque

Application web academique developpee avec **Flask + SQLite + HTML/CSS** pour la gestion d'une bibliotheque.

## Objectif du projet

Permettre la gestion complete d'une bibliotheque avec deux profils:
- **Administrateur**: supervision globale et validation des operations.
- **Usager**: consultation du catalogue, demandes d'emprunt, reservations et suivi personnel.

## Fonctionnalites principales

### Authentification et roles
- Inscription d'un usager.
- Connexion / deconnexion.
- Gestion des permissions par role (`admin`, `user`).

### Cote usager
- Dashboard personnel avec:
  - indicateurs (emprunts actifs, retards, demandes en attente, reservations actives),
  - alertes (retards, echeances proches),
  - activite recente,
  - suggestions d'ouvrages disponibles.
- Consultation du catalogue.
- Recherche multi-criteres (titre, auteur, ISBN, editeur, annee).
- Demande d'emprunt.
- Reservation d'ouvrage.
- Suivi des demandes, emprunts et reservations.

### Cote administrateur
- Dashboard global (statistiques systeme).
- Gestion des ouvrages (ajout + recherche + stock).
- Gestion des comptes usagers/admin.
- Gestion des demandes d'emprunt:
  - approbation/rejet,
  - **date de remise obligatoire** a la validation.
- Gestion des retours (cloture d'emprunt).
- Gestion des reservations (cloture).

## Base de donnees

- SGBD: **SQLite** (`library.db`).
- La base est creee automatiquement au premier lancement.
- Le schema contient notamment:
  - `users`
  - `books`
  - `loan_requests`
  - `loans`
  - `reservations`

## Donnees initiales

Le projet contient un jeu de donnees d'ouvrages (classiques et contemporains ivoiriens) deja injecte dans la base locale actuelle.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement

```powershell
python app.py
```

Ouvrir ensuite: `http://127.0.0.1:5000`

## Compte administrateur par defaut

- Email: `admin@bibliotheque.local`
- Mot de passe: `admin1234`

## Structure principale

- `app.py` : logique Flask (routes, auth, roles, workflow metier)
- `templates/` : interfaces Jinja2 (admin/user)
- `static/style.css` : style moderne et responsive
- `library.db` : base SQLite locale
- `requirements.txt` : dependances Python

## Demonstration conseillee (academique)

1. Connexion en usager.
2. Recherche d'un ouvrage dans le catalogue.
3. Creation d'une demande d'emprunt.
4. Connexion admin puis validation avec date de remise.
5. Retour en usager pour voir la mise a jour du dashboard.
6. Cloture du retour cote admin.

## Limites connues (hors perimetre academique)

- Pas de tests automatises complets.
- Pas de pipeline de deploiement/monitoring.
- Gestion avancee des mots de passe (reset/email) non incluse.
