from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', _('1. Administrateur Système')
    DIRECTOR = 'DIRECTOR', _('2. Directeur / Gérant')
    RECEPTIONIST = 'RECEPTIONIST', _('3. Réceptionniste')
    BOOKING_AGENT = 'BOOKING_AGENT', _('4. Agent de Réservation')
    HOUSEKEEPING_MGR = 'HOUSEKEEPING_MGR', _('5. Responsable Housekeeping')
    HOUSEKEEPER = 'HOUSEKEEPER', _('6. Femme / Valet de Chambre')
    MAINTENANCE_MGR = 'MAINTENANCE_MGR', _('7. Responsable Maintenance')
    TECHNICIAN = 'TECHNICIAN', _('8. Technicien Maintenance')
    ACCOUNTANT = 'ACCOUNTANT', _('9. Comptable')
    CASHIER = 'CASHIER', _('10. Caissier')
    RESTAURANT_MGR = 'RESTAURANT_MGR', _('11. Responsable Restaurant')
    WAITER = 'WAITER', _('12. Serveur')
    KITCHEN_MGR = 'KITCHEN_MGR', _('13. Chef Cuisine')
    COOK = 'COOK', _('14. Cuisinier')
    STOREKEEPER = 'STOREKEEPER', _('15. Magasinier')
    HR_MGR = 'HR_MGR', _('16. Responsable RH')
    COMMERCIAL_MGR = 'COMMERCIAL_MGR', _('17. Responsable Commercial')
    NIGHT_AUDITOR = 'NIGHT_AUDITOR', _('18. Night Auditor (Clôture)')

class User(AbstractUser):
    username = models.CharField(_('username'), max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(_('Adresse email'), unique=True)
    phone = models.CharField(_('Numéro de téléphone'), max_length=20, blank=True, null=True)
    role = models.CharField(
        _('Rôle Système'),
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.RECEPTIONIST
    )
    department = models.CharField(_('Département / Service'), max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def display_name(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.email

    # Helper properties for permission checks
    @property
    def is_admin_role(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_director_role(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR] or self.is_superuser

    @property
    def is_reception_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.RECEPTIONIST, UserRole.BOOKING_AGENT, UserRole.NIGHT_AUDITOR]

    @property
    def is_housekeeping_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.HOUSEKEEPING_MGR, UserRole.HOUSEKEEPER]

    @property
    def is_maintenance_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.MAINTENANCE_MGR, UserRole.TECHNICIAN]

    @property
    def is_restaurant_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.RESTAURANT_MGR, UserRole.WAITER]

    @property
    def is_kitchen_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.KITCHEN_MGR, UserRole.COOK]

    @property
    def is_storekeeper_role(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.STOREKEEPER]

    @property
    def is_cashier_role(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CASHIER, UserRole.ACCOUNTANT, UserRole.NIGHT_AUDITOR]

    @property
    def is_finance_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.ACCOUNTANT, UserRole.NIGHT_AUDITOR]

    @property
    def is_hr_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.HR_MGR]

    @property
    def is_commercial_staff(self):
        return self.role in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.COMMERCIAL_MGR]


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Activité Utilisateur')
        verbose_name_plural = _('Activités Utilisateurs')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.action} à {self.timestamp}"
