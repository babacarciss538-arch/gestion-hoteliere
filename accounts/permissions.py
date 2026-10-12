from functools import wraps
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

# Méthodes HTTP considérées comme "lecture seule".
SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

# Rôles d'administration et de direction soumis aux restrictions en lecture seule
ADMIN_DIRECTOR_ROLES = {'ADMIN', 'DIRECTOR'}

# Opérations financières sensibles (remboursements, annulations, corrections) :
SENSITIVE_FINANCE_ROLES = ['DIRECTOR']


class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier qu'un utilisateur possède l'un des rôles autorisés."""
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            return True
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les autorisations nécessaires pour accéder à ce module.")
        return super().handle_no_permission()


def role_required(allowed_roles):
    """Décorateur de vue pour contrôler l'accès par rôle."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())

            if request.user.is_superuser or request.user.role == 'ADMIN' or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            raise PermissionDenied("Accès refusé. Permission insuffisante pour votre rôle.")
        return _wrapped_view
    return decorator


def role_required_for_write(read_roles, write_roles):
    """Lecture (GET/HEAD/OPTIONS) pour read_roles, écriture (POST, etc.) pour write_roles.

    Le contrôle est fait côté serveur : un POST direct d'un rôle non autorisé
    est refusé (403) avant tout traitement de formulaire.
    """
    def decorator(view_func):
        read_view = role_required(read_roles)(view_func)
        write_view = role_required(write_roles)(view_func)

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method in SAFE_METHODS:
                return read_view(request, *args, **kwargs)
            return write_view(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def is_admin_or_director(user):
    """Vérifie si un utilisateur est Administrateur ou Directeur (ou superutilisateur)."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or getattr(user, 'role', '') in ADMIN_DIRECTOR_ROLES


def enforce_read_only_for_admin_and_director(view_func):
    """CHANTIER 7 :
    Pour Housekeeping, Maintenance, Restaurant POS, Magasin & Stock :
    L'Administrateur et le Directeur sont STRICTEMENT en lecture seule.
    Toute tentative d'écriture (POST, PUT, PATCH, DELETE) lève immédiatement PermissionDenied (403).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method not in SAFE_METHODS and is_admin_or_director(request.user):
            raise PermissionDenied(
                "Opération d'écriture interdite : l'Administrateur et le Directeur disposent d'un accès strictement en lecture seule sur ce module."
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def sensitive_finance_required(view_func):
    """À poser sur les vues de remboursement, annulation ou correction financière."""
    return role_required(SENSITIVE_FINANCE_ROLES)(view_func)