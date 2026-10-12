from django.core.exceptions import PermissionDenied


def not_commercial_required(view_func):
    """Interdit l'accès au Responsable Commercial sur le module Achats / Stock."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'role') and request.user.role == 'COMMERCIAL':
            raise PermissionDenied("Accès interdit au Responsable Commercial.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def storekeeper_or_admin_required(view_func):
    """Réservé au Magasinier ou Admin. Interdit la gestion directe de stock aux cuisiniers et commerciaux."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        user_role = getattr(request.user, 'role', None)
        if user_role in ['COMMERCIAL', 'KITCHEN', 'CHEF'] and not request.user.is_superuser:
            raise PermissionDenied("Action réservée au magasinier et à l'administration.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view