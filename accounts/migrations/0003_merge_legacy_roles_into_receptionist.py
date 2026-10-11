from django.db import migrations


LEGACY_ROLES = ('BOOKING_AGENT', 'CASHIER', 'ACCOUNTANT')


def merge_legacy_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for role in LEGACY_ROLES:
        User.objects.filter(role=role).update(role='RECEPTIONIST', legacy_role=role)


def restore_legacy_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for role in LEGACY_ROLES:
        User.objects.filter(role='RECEPTIONIST', legacy_role=role).update(role=role, legacy_role='')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_legacy_role_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(merge_legacy_roles, restore_legacy_roles),
    ]