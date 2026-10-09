from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, UserProfileForm
from .models import UserActivity

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Enregistrement dans l'activité utilisateur
            client_ip = getattr(request, 'client_ip', None)
            UserActivity.objects.create(
                user=user,
                action="Connexion réussie",
                ip_address=client_ip
            )
            
            messages.success(request, f"Bienvenue {user.display_name} !")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Identifiants incorrects. Veuillez vérifier votre email et mot de passe.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        client_ip = getattr(request, 'client_ip', None)
        UserActivity.objects.create(
            user=request.user,
            action="Déconnexion",
            ip_address=client_ip
        )
        logout(request)
        messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('accounts:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    activities = request.user.activities.all()[:10]
    return render(request, 'accounts/profile.html', {
        'form': form,
        'activities': activities
    })
