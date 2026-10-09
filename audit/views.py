from django.shortcuts import render
from accounts.models import UserActivity
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'NIGHT_AUDITOR'])
def audit_index(request):
    activities = UserActivity.objects.select_related('user').all()[:100]
    return render(request, 'audit/index.html', {'activities': activities})
