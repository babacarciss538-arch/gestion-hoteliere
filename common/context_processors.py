from django.conf import settings

def hotel_context(request):
    """Context processor global pour injecter le nom de l'hôtel, la devise (FCFA) et le rôle de l'utilisateur."""
    user_role = None
    if request.user.is_authenticated:
        user_role = getattr(request.user, 'role', 'USER')
        
    return {
        'HOTEL_NAME': getattr(settings, 'HOTEL_NAME', 'Hôtel Prestige & Spa'),
        'HOTEL_CURRENCY': getattr(settings, 'HOTEL_CURRENCY', 'FCFA'),
        'CURRENT_USER_ROLE': user_role,
    }
