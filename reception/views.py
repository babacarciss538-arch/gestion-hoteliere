from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'RECEPTIONIST', 'BOOKING_AGENT', 'NIGHT_AUDITOR'])
def reception_index(request):
    return render(request, 'reception/index.html')
