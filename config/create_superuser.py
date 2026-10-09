import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Modifiez avec vos identifiants souhaités
USERNAME = 'admin'
EMAIL = 'admin@hotel.com'
PASSWORD = 'Killifeugui538'

if not User.objects.filter(username=USERNAME).exists():
    print(f"Création du superutilisateur {USERNAME}...")
    User.objects.create_superuser(username=USERNAME, email=EMAIL, password=PASSWORD)
    print("Superutilisateur créé avec succès !")
else:
    print(f"Le superutilisateur {USERNAME} existe déjà.")