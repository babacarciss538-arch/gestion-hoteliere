from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from accounts.models import User, UserRole
from cashier.models import CashDiscrepancy, CashSession
from finance.models import Expense, Invoice, Payment, Refund, Tax
from guests.models import Guest
from reception.models import CheckIn
from reservations.models import Reservation, ReservationStatus
from rooms.models import Room, RoomStatus


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class ReceptionistRoleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reception@example.com',
            email='reception@example.com',
            password='test-password-123',
            first_name='Camille',
            last_name='Reception',
            role=UserRole.RECEPTIONIST,
        )

    def test_role_choices_exclude_merged_roles(self):
        role_values = {value for value, label in UserRole.choices}
        self.assertEqual(UserRole.RECEPTIONIST.label, 'Réceptionniste')
        self.assertFalse({'BOOKING_AGENT', 'CASHIER', 'ACCOUNTANT'} & role_values)
        self.assertIn('NIGHT_AUDITOR', role_values)

    def test_login_redirects_to_shared_reception_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': self.user.email,
            'password': 'test-password-123',
        })
        self.assertRedirects(response, reverse('dashboard:index'))

        response = self.client.get(reverse('dashboard:index'))
        self.assertTemplateUsed(response, 'dashboards/reception.html')
        self.assertContains(response, 'Réservations')
        self.assertContains(response, 'Check-In / Check-Out')
        self.assertContains(response, 'Factures et paiements')
        self.assertContains(response, reverse('reports:index'))
        self.assertNotContains(response, 'Journal d\'Audit')

    def test_receptionist_can_access_operational_and_financial_routes(self):
        self.client.force_login(self.user)
        for route_name in (
            'reservations:list',
            'guests:list',
            'rooms:list',
            'reception:index',
            'cashier:index',
            'finance:index',
            'reports:index',
        ):
            with self.subTest(route=route_name):
                self.assertEqual(self.client.get(reverse(route_name)).status_code, 200)

    def test_reservations_can_be_searched_and_edited(self):
        guest = Guest.objects.create(first_name='Amina', last_name='Diop', email='amina@example.com')
        room = Room.objects.create(number='202', status=RoomStatus.RESERVED)
        reservation = Reservation.objects.create(
            guest=guest,
            room=room,
            check_in_date=timezone.localdate(),
            status=ReservationStatus.CONFIRMED,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reservations:list'), {'q': 'amina'})
        self.assertContains(response, reservation.reference)
        self.assertNotContains(response, 'Aucune réservation enregistrée.')

        response = self.client.post(reverse('reservations:edit', args=[reservation.pk]), {
            'guest': guest.pk,
            'room': room.pk,
            'check_in_date': timezone.localdate().isoformat(),
            'check_out_date': '',
            'status': ReservationStatus.CANCELLED,
        })
        self.assertRedirects(response, reverse('reservations:list'))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_check_in_and_check_out_update_related_hotel_records(self):
        guest = Guest.objects.create(first_name='Moussa', last_name='Fall')
        room = Room.objects.create(number='303', status=RoomStatus.RESERVED)
        reservation = Reservation.objects.create(
            guest=guest,
            room=room,
            check_in_date=timezone.localdate(),
            status=ReservationStatus.CONFIRMED,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reception:index'), {
            'action': 'check_in',
            'reservation_id': reservation.pk,
        })
        self.assertRedirects(response, reverse('reception:index'))
        check_in = CheckIn.objects.get(reservation=reservation)
        room.refresh_from_db()
        self.assertEqual(room.status, RoomStatus.OCCUPIED)
        self.assertIsNotNone(check_in.actual_check_in)

        response = self.client.post(reverse('reception:index'), {
            'action': 'check_out',
            'check_in_id': check_in.pk,
        })
        self.assertRedirects(response, reverse('reception:index'))
        check_in.refresh_from_db()
        reservation.refresh_from_db()
        room.refresh_from_db()
        self.assertIsNotNone(check_in.actual_check_out)
        self.assertEqual(reservation.status, ReservationStatus.COMPLETED)
        self.assertEqual(room.status, RoomStatus.TO_CLEAN)

    def test_finance_page_lists_existing_records_read_only(self):
        invoice = Invoice.objects.create(amount=900)
        payment = Payment.objects.create(amount=325)
        Expense.objects.create(label='Électricité', amount=80, category='Services')
        Tax.objects.create(name='TVA', amount=15)
        Refund.objects.create(payment=payment, amount=20, reason='Correction')
        self.client.force_login(self.user)

        response = self.client.get(reverse('finance:index'))
        self.assertContains(response, f'#{invoice.pk}')
        self.assertContains(response, '325')
        self.assertContains(response, 'Électricité')
        self.assertContains(response, 'TVA')
        self.assertContains(response, 'Correction')

    def test_receptionist_cannot_access_audit_journal(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('audit:index'))
        self.assertEqual(response.status_code, 403)

    def test_admin_and_director_keep_their_module_access(self):
        for role in (UserRole.ADMIN, UserRole.DIRECTOR):
            user = User.objects.create_user(
                username=f'{role.lower()}@example.com',
                email=f'{role.lower()}@example.com',
                password='test-password-123',
                role=role,
            )
            with self.subTest(role=role):
                self.client.force_login(user)
                for route_name in ('cashier:index', 'finance:index', 'reports:index', 'audit:index'):
                    self.assertEqual(self.client.get(reverse(route_name)).status_code, 200)

    def test_cashier_sessions_are_owned_and_can_be_closed(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cashier:index'), {'action': 'open', 'opening_amount': '100.00'})
        session = CashSession.objects.get(cashier=self.user, is_closed=False)

        second_open = self.client.post(reverse('cashier:index'), {
            'action': 'open',
            'opening_amount': '200.00',
        })
        self.assertEqual(second_open.status_code, 200)
        self.assertEqual(CashSession.objects.filter(cashier=self.user, is_closed=False).count(), 1)

        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='test-password-123',
            role=UserRole.RECEPTIONIST,
        )
        other_session = CashSession.objects.create(cashier=other_user, opening_amount=50)
        denied_close = self.client.post(reverse('cashier:index'), {
            'action': 'close',
            'session_id': other_session.pk,
            'closing_amount': '50.00',
        })
        self.assertEqual(denied_close.status_code, 404)

        negative_close = self.client.post(reverse('cashier:index'), {
            'action': 'close',
            'session_id': session.pk,
            'closing_amount': '-1.00',
        })
        self.assertEqual(negative_close.status_code, 200)
        session.refresh_from_db()
        self.assertFalse(session.is_closed)

        response = self.client.post(reverse('cashier:index'), {
            'action': 'close',
            'session_id': session.pk,
            'closing_amount': '120.00',
        })
        self.assertRedirects(response, reverse('cashier:index'))
        session.refresh_from_db()
        self.assertTrue(session.is_closed)
        self.assertEqual(session.closing_amount, 120)
        self.assertIsNotNone(session.closed_at)

    def test_financial_dashboard_values_come_from_database(self):
        Payment.objects.create(amount=325)
        Invoice.objects.create(amount=900)
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['today_payments'], 325)
        self.assertEqual(response.context['invoice_count'], 1)
        self.assertEqual(response.context['invoice_total'], 900)

    def test_cash_discrepancies_on_dashboard_are_scoped_to_own_sessions(self):
        own_session = CashSession.objects.create(cashier=self.user, opening_amount=100)
        other_user = User.objects.create_user(
            username='cashier-other@example.com',
            email='cashier-other@example.com',
            password='test-password-123',
            role=UserRole.RECEPTIONIST,
        )
        other_session = CashSession.objects.create(cashier=other_user, opening_amount=100)
        CashDiscrepancy.objects.create(session=own_session, expected_amount=100, actual_amount=90)
        CashDiscrepancy.objects.create(session=other_session, expected_amount=100, actual_amount=110)
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['cash_discrepancy_count'], 1)
        self.assertEqual(list(response.context['cash_sessions']), [own_session])

    def test_payment_requires_own_open_session_and_respects_linked_invoice_balance(self):
        invoice = Invoice.objects.create(amount=250)
        self.client.force_login(self.user)

        no_session = self.client.post(reverse('finance:index'), {
            'invoice': invoice.pk,
            'amount': '100.00',
        })
        self.assertEqual(no_session.status_code, 200)
        self.assertEqual(Payment.objects.count(), 0)

        self.client.post(reverse('cashier:index'), {
            'action': 'open',
            'opening_amount': '50.00',
        })
        session = CashSession.objects.get(cashier=self.user, is_closed=False)
        response = self.client.post(reverse('finance:index'), {
            'invoice': invoice.pk,
            'amount': '100.00',
        })
        self.assertRedirects(response, reverse('finance:index'))
        payment = Payment.objects.get()
        self.assertEqual(payment.invoice_id, invoice.pk)
        self.assertEqual(payment.cash_session_id, session.pk)

        overpayment = self.client.post(reverse('finance:index'), {
            'invoice': invoice.pk,
            'amount': '151.00',
        })
        self.assertEqual(overpayment.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)


class LegacyRoleMigrationTests(TransactionTestCase):
    migrate_from = ('accounts', '0001_initial')
    migrate_to = ('accounts', '0003_merge_legacy_roles_into_receptionist')
    legacy_roles = ('BOOKING_AGENT', 'CASHIER', 'ACCOUNTANT')

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        HistoricalUser = old_apps.get_model('accounts', 'User')
        self.user_details = {}

        for index, role in enumerate(self.legacy_roles, start=1):
            user = HistoricalUser.objects.create(
                username=f'legacy-{index}@example.com',
                email=f'legacy-{index}@example.com',
                password=make_password('unchanged-password'),
                first_name='Legacy',
                last_name=f'User {index}',
                phone=f'555000{index}',
                role=role,
            )
            self.user_details[role] = {
                'pk': user.pk,
                'password': user.password,
                'date_joined': user.date_joined,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
            }
            session = CashSession.objects.create(cashier_id=user.pk, opening_amount=100 + index)
            self.user_details[role]['cash_session_pk'] = session.pk

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.migrated_apps = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_converts_and_reverses_roles_without_recreating_users(self):
        MigratedUser = self.migrated_apps.get_model('accounts', 'User')
        for old_role, details in self.user_details.items():
            user = MigratedUser.objects.get(pk=details['pk'])
            self.assertEqual(user.role, 'RECEPTIONIST')
            self.assertEqual(user.legacy_role, old_role)
            self.assertEqual(user.password, details['password'])
            self.assertEqual(user.date_joined, details['date_joined'])
            self.assertEqual(user.first_name, details['first_name'])
            self.assertEqual(user.last_name, details['last_name'])
            self.assertEqual(user.phone, details['phone'])
            self.assertTrue(CashSession.objects.filter(
                pk=details['cash_session_pk'], cashier_id=details['pk'],
            ).exists())

        executor = MigrationExecutor(connection)
        executor.migrate([('accounts', '0002_user_legacy_role_alter_user_role')])
        restored_apps = executor.loader.project_state([
            ('accounts', '0002_user_legacy_role_alter_user_role'),
        ]).apps
        RestoredUser = restored_apps.get_model('accounts', 'User')

        for old_role, details in self.user_details.items():
            user = RestoredUser.objects.get(pk=details['pk'])
            self.assertEqual(user.role, old_role)
            self.assertEqual(user.legacy_role, '')
            self.assertEqual(user.password, details['password'])