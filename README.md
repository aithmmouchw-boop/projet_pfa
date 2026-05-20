# CLINOVA — application Django

Gestion de clinique (patients, médecins, rendez-vous, facturation, etc.). Base de données **MySQL** (PyMySQL).

## Prérequis

- Python 3.11+ (3.14 utilisé ici fonctionne)
- Serveur **MySQL** démarré (utilisateur avec droit `CREATE DATABASE` pour la première installation)

## Arborescence utile

- `manage.py` — point d’entrée Django
- `config/settings.py` — configuration (charge `.env` à la racine de ce dossier)
- `.env.example` — modèle de variables ; copiez vers `.env` et adaptez
- `scripts/create_mysql_db.py` — crée la base `DB_NAME` si elle n’existe pas

## Installation sur une nouvelle machine

Depuis le dossier `PROJET_PYTHON` :

1. **Environnement virtuel** (recommandé : `.venv` ici, ou utilisez le dossier `env` au niveau parent `projet PFA`).

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Fichier `.env`** : copiez `.env.example` vers `.env` et renseignez `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Sous **Windows**, ne définissez pas `DB_SOCKET` (laissez la ligne absente ou vide) pour utiliser TCP.

3. **Base de données** :

   ```powershell
   python scripts/create_mysql_db.py
   python manage.py migrate
   python manage.py seed_clinic
   ```

4. **Lancer le site** :

   ```powershell
   python manage.py runserver
   ```

   Ouvrez [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Comptes de démo (`seed_clinic`)

| Rôle    | E-mail                     | Mot de passe |
|---------|----------------------------|--------------|
| (tous)  | `*@CLINOVA.local`       | `demo12345`  |

Exemples : `patient@CLINOVA.local`, `medecin@CLINOVA.local`, `caissier@CLINOVA.local`, `secretaire@CLINOVA.local`.

## Dépannage

- **Erreur 1049 (base inconnue)** : exécutez `python scripts/create_mysql_db.py` ou créez la base à la main dans MySQL.
- **Erreur 2003 / connexion refusée** : MySQL n’écoute pas sur l’hôte/port indiqués ; vérifiez le service Windows « MySQL » et le port dans `.env`.
- **Clé trop longue (1071)** : le modèle utilisateur impose un e-mail unique en `varchar(191)` pour rester compatible utf8mb4 ; ne remontez pas ce champ sans ajuster l’index MySQL.
