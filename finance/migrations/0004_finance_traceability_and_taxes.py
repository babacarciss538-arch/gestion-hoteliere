import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_legacy_invoice_subtotal(apps, schema_editor):
    """Anciennes factures : sous-total = montant existant, taxe incluse = 0.
    Aucune donnée n'est supprimée ni modifiée dans `amount`."""
    Invoice = apps.get_model('finance', 'Invoice')
    Invoice.objects.filter(subtotal=0).update(subtotal=models.F('amount'))


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_payment_cash_session_payment_invoice'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoice',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoice',
            name='customer_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='invoice',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='invoice',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='invoice',
            name='tax_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='payment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='refund',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tax',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tax',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tax',
            name='rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='taxes',
            field=models.ManyToManyField(blank=True, related_name='invoices', to='finance.tax'),
        ),
        migrations.RunPython(fill_legacy_invoice_subtotal, migrations.RunPython.noop),
    ]