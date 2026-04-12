#!/usr/bin/env python
"""
Script de configuration initiale pour LASPAD Event.
Lance ce script après avoir créé le virtualenv et installé les dépendances.

Usage :
    python setup.py
"""

import os
import sys
import subprocess


def run(cmd, **kwargs):
    print(f"\n▶  {cmd}")
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        print(f"❌ Erreur lors de : {cmd}")
        sys.exit(1)
    return result


def main():
    print("=" * 55)
    print("  LASPAD Event — Configuration initiale")
    print("=" * 55)

    # 1. Copier .env
    if not os.path.exists('.env'):
        run('cp .env.example .env')
        print("✅ Fichier .env créé — pensez à renseigner vos clés !")
    else:
        print("✅ Fichier .env déjà existant.")

    # 2. Migrations
    run('python manage.py makemigrations')
    run('python manage.py migrate')
    print("✅ Base de données migrée.")

    # 3. Créer le superuser
    print("\n" + "─" * 40)
    print("Création du compte administrateur LASPAD :")
    run('python manage.py createsuperuser')

    # 4. Collecte des fichiers statiques
    run('python manage.py collectstatic --noinput')
    print("✅ Fichiers statiques collectés.")

    # 5. Message final
    print("\n" + "=" * 55)
    print("  ✅ Installation terminée !")
    print("=" * 55)
    print("\nPour lancer le serveur :")
    print("  python manage.py runserver")
    print("\nDashboard admin :")
    print("  http://localhost:8000/dashboard/")
    print("\nSite public :")
    print("  http://localhost:8000/")
    print()


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    main()
