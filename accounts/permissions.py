from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from functools import wraps

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
