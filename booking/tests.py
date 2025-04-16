from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from .models import Room, Reservation, UserProfile
from .forms import SignupForm


class BookingFlowTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tester',
            password='pass12345',
            email='tester@example.com'
        )
        UserProfile.objects.create(user=self.user, phone='987654321')
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.room = Room.objects.create(
            room_number='101',
            room_type='Deluxe',
            description='Test room',
            price_per_night=100.00
        )

    def test_that_true_is_true(self):
        self.assertTrue(True)

    def test_profile_page_is_displayed(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.get(reverse('moj_ucet'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Môj účet")

    def test_user_can_delete_account(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.post(reverse('delete_account'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='tester').exists())

    def test_user_registration_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '123456789',
            'password': 'securepassword123',
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save()
        self.assertEqual(User.objects.count(), 3)  # dvaja zo setUp + nový
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('securepassword123'))

    def test_create_reservation_manually(self):
        check_in = date.today()
        check_out = check_in + timedelta(days=3)
        reservation = Reservation.objects.create(
            user=self.user,
            room=self.room,
            check_in=check_in,
            check_out=check_out,
            total_price=3 * self.room.price_per_night
        )
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(reservation.total_price, 300.00)

    def test_anonymous_user_redirected_from_account(self):
        response = self.client.get(reverse('moj_ucet'))
        self.assertRedirects(response, '/accounts/login/?next=/moj_ucet/')

    def test_anonymous_user_redirected_from_reservation(self):
        response = self.client.get(reverse('create_reservation'))
        self.assertRedirects(response, '/accounts/login/?next=/reservations/new/')

    def test_homepage_loads_successfully(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
