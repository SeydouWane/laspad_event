# LASPAD Event

Plateforme de gestion d'événements scientifiques du **LASPAD** (Laboratoire d'Analyses Statistiques Pour l'Aide à la Décision).

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11 + Django 4.2 |
| Frontend | Tailwind CSS 3 |
| Base de données | PostgreSQL 15 |
| Tâches asynchrones | Celery + Redis |
| Email | SMTP (Gmail ou SendGrid) |
| Calendrier | Google Calendar API |

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/VOTRE-USERNAME/laspad_event.git
cd laspad_event
```

### 2. Créer le virtualenv et installer les dépendances

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Editez `.env` et renseignez :
- `SECRET_KEY` — clé secrète Django
- `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD` — SMTP Gmail
- `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` — Google Calendar API

### 4. Créer la base de données PostgreSQL

```sql
-- Dans psql
CREATE DATABASE laspad_event;
```

> Les paramètres par défaut : user=`postgres`, password=`aipenpass123`, host=`localhost`

### 5. Configurer Tailwind CSS

```bash
python manage.py tailwind install
python manage.py tailwind build
```

### 6. Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Créer le superutilisateur

```bash
python manage.py createsuperuser
```

### 8. Lancer le serveur

```bash
python manage.py runserver
```

---

## URLs principales

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Page d'accueil — liste des événements |
| `http://localhost:8000/e/<slug>/` | Détail d'un événement |
| `http://localhost:8000/inscription/<slug>/` | Formulaire d'inscription |
| `http://localhost:8000/dashboard/` | Dashboard administrateur |
| `http://localhost:8000/dashboard/login/` | Connexion admin |
| `http://localhost:8000/admin/` | Admin Django natif |

---

## Structure du projet

```
laspad_event/
├── config/                  # Settings, URLs, Celery, WSGI
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── events/                  # App événements
│   ├── models.py            # Event, Location, Organizer
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── registrations/           # App inscriptions
│   ├── models.py            # Registration, Participant
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── notifications/           # App notifications
│   ├── email_service.py     # Envoi d'emails
│   ├── calendar_service.py  # Google Calendar API
│   ├── tasks.py             # Tâches Celery
│   └── templatetags/        # Filtres Django
├── dashboard/               # App dashboard admin
│   ├── views.py
│   └── urls.py
├── templates/               # Templates HTML
│   ├── base/                # Layout + navbar + footer
│   ├── events/              # Pages publiques événements
│   ├── registrations/       # Formulaires inscription
│   ├── dashboard/           # Interface admin
│   └── emails/              # Templates emails HTML
├── static/                  # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── img/                 # ← Placer logo.png ici
├── theme/                   # App Tailwind CSS
├── media/                   # Uploads (banners, photos)
├── .env.example
├── requirements.txt
└── manage.py
```

---

## Fonctionnalités

### Gestion des événements
- Création d'événements (webinaire, conférence, atelier, séminaire)
- Support en ligne (Meet, Zoom, YouTube) et présentiel
- Capacité limitée ou illimitée
- Statuts : Brouillon → Publié → Terminé / Annulé

### Inscriptions
- **Mode direct** : inscription acceptée automatiquement
- **Mode validation** : admin accepte ou refuse manuellement
- Lien unique par inscription (token UUID)

### Notifications automatiques
- Email de confirmation / accusé de réception
- Email de validation ou refus
- Rappels 24h et 1h avant l'événement (via Celery Beat)
- Email d'annulation

### Google Calendar
- **Option A** : bouton "Ajouter à Google Calendar" (sans API)
- **Option B** : insertion directe via Google Calendar API v3

### Dashboard admin
- Statistiques globales (événements, inscriptions, participants)
- Validation des inscriptions en un clic
- Export CSV par événement
- Filtrage des inscriptions par statut

---

## Tâches Celery (rappels automatiques)

```bash
# Dans un terminal séparé, lancer Redis
redis-server

# Lancer le worker Celery
celery -A config worker -l info

# Lancer le scheduler (rappels automatiques)
celery -A config beat -l info
```

---

## Google Calendar API — Configuration

1. Accéder à [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet → Activer l'API Google Calendar
3. Créer des identifiants OAuth 2.0
4. Renseigner `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` dans `.env`

---

## Déploiement (production)

```bash
# Variables d'environnement
DEBUG=False
ALLOWED_HOSTS=votre-domaine.sn

# Collecte des statiques
python manage.py collectstatic

# Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## Ajouter le logo LASPAD

Placez le fichier `logo.png` dans :
```
static/img/logo.png
```

---

## Licence

Projet développé pour le LASPAD — Dakar, Sénégal.
