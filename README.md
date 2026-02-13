```markdown
# 📚 Gestion d’une Bibliothèque

Application web académique développée avec **Flask + SQLite + HTML/CSS** pour la gestion d’une bibliothèque universitaire.  
Ce projet illustre la transition entre la **modélisation UML** et la **réalisation technique**.

---

## 🎯 Objectifs du projet
- Concevoir un modèle UML complet pour gérer une bibliothèque (emprunts, retours, réservations, gestion des usagers et des ouvrages).  
- Réaliser les diagrammes de **cas d’utilisation**, **séquence** et **classes** pour décrire le fonctionnement.  
- Développer une application web académique avec interfaces **usager** et **administrateur**.  
- Mobiliser les compétences en **modélisation orientée objet**, **gestion de base de données** et **développement web en Python**.  

---

## 🛠️ Technologies utilisées
- **Backend** : Python (Flask)  
- **Frontend** : HTML/CSS + Jinja2  
- **Base de données** : SQLite (`library.db`)  
- **Modélisation UML** : StarUML / PlantUML  

---

## 👥 Profils utilisateurs
### Usager (Adhérent)
- Inscription et authentification.  
- Consultation du catalogue et recherche multi-critères.  
- Demandes d’emprunt et réservations.  
- Suivi du tableau de bord personnel (emprunts actifs, retards, réservations).  

### Administrateur
- Supervision globale via un tableau de bord.  
- Gestion des ouvrages et des comptes usagers.  
- Validation ou rejet des demandes d’emprunt avec date limite obligatoire.  
- Enregistrement des retours et clôture des réservations.  
- Suspension manuelle ou automatique des usagers.  

---

## 📂 Structure du projet
- `app.py` : logique Flask (routes, authentification, workflow métier).  
- `templates/` : interfaces HTML/Jinja2 (usager et administrateur).  
- `static/style.css` : style moderne et responsive.  
- `library.db` : base SQLite locale.  
- `requirements.txt` : dépendances Python.  

---

## ⚙️ Installation
```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.\.venv\Scripts\Activate.ps1 # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## 🚀 Lancement
```bash
python app.py
```
Puis ouvrir dans le navigateur :  
`http://127.0.0.1:5000`

---

## 🔑 Compte administrateur par défaut
- Email : `admin@bibliotheque.local`  
- Mot de passe : `admin1234`  

---

## 🗄️ Base de données
La base est créée automatiquement au premier lancement.  
Tables principales :  
- `users` : gestion des usagers et administrateurs.  
- `books` : catalogue des ouvrages.  
- `loan_requests` : demandes d’emprunt.  
- `loans` : emprunts validés.  
- `reservations` : réservations actives ou clôturées.  

---

## 🎬 Démonstration académique
1. Connexion en usager.  
2. Recherche d’un ouvrage dans le catalogue.  
3. Création d’une demande d’emprunt.  
4. Connexion administrateur → validation avec date limite.  
5. Retour en usager → mise à jour du tableau de bord.  
6. Clôture du retour côté administrateur.  

---

## ⚠️ Limites connues
- Pas de réinitialisation de mot de passe par email.  
- Pas de pipeline de déploiement/monitoring.  
- Tests automatisés non inclus.  

---

## 🔮 Perspectives d’amélioration
- Mise en place de tests unitaires et fonctionnels.  
- Renforcement de la sécurité (hashage avancé, protection CSRF/XSS).  
- Interface plus moderne avec frameworks front-end (Bootstrap, TailwindCSS).  
- Notifications par email/SMS pour les échéances d’emprunt.  
- Déploiement sur un serveur cloud avec CI/CD.  

---

## 👨‍🎓 Contexte académique
Ce projet a été réalisé dans le cadre du module de **Génie Logiciel** à l’Université Félix Houphouët-Boigny.  
Il illustre la mise en pratique des concepts de modélisation UML et de développement web en Python.  

---
```
