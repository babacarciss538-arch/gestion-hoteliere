import json

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Stockage temporaire de l'IP du client sur la requête
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.client_ip = x_forwarded_for.split(',')[0]
        else:
            request.client_ip = request.META.get('REMOTE_ADDR')

        response = self.get_response(request)
        return response
