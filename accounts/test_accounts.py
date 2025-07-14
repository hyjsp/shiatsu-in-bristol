import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta, time
from django.contrib.auth import get_user_model
from products.models import Category, Product, Booking
from accounts.models import CustomUser

User = get_user_model()

# --- Original User/Account Tests ---
class CustomUserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="will", email="will@email.com", password="testpass123"
        )
        self.assertEqual(user.username, "will")
        self.assertEqual(user.email, "will@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username="superadmin", email="superadmin@email.com", password="testpass123"
        )
        self.assertEqual(admin_user.username, "superadmin")
        self.assertEqual(admin_user.email, "superadmin@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

class AccountsFlowTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser", email="testuser@email.com", password="testpass123"
        )

    def test_user_registration(self):
        response = self.client.post(reverse('account_signup'), {
            'email': 'newuser@email.com',
            'password1': 'newpass12345',
            'password2': 'newpass12345',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(self.User.objects.filter(email='newuser@email.com').exists())

    def test_login_logout(self):
        login = self.client.login(email="testuser@email.com", password="testpass123")
        self.assertTrue(login)
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset(self):
        response = self.client.post(reverse('account_reset_password'), {
            'email': 'testuser@email.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testuser@email.com', mail.outbox[0].to)

# --- New Booking/Profile Tests ---
# (All the booking/profile tests from the current file go here, unchanged)

# --- Fixtures ---
@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(transactional_db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def other_user(transactional_db):
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123'
    )

@pytest.fixture
def category(transactional_db):
    return Category.objects.create(name='Shiatsu Sessions')

@pytest.fixture
def product(transactional_db, category):
    return Product.objects.create(
        name='60-Minute Session',
        description='A relaxing 60-minute session',
        price=65.00,
        duration_minutes=60,
        category=category,
        is_active=True
    )

@pytest.fixture
def booking(transactional_db, user, product):
    tomorrow = timezone.now().date() + timedelta(days=1)
    return Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(14, 0),
        notes='Test booking'
    )

# --- Profile Page Tests ---
def test_profile_page_authenticated(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('account:profile'))
    assert response.status_code == 200
    assert 'My Profile' in response.content.decode()
    assert '60-Minute Session' in response.content.decode()
    assert 'Test booking' in response.content.decode()

def test_profile_page_unauthenticated(transactional_db, client):
    response = client.get(reverse('account:profile'))
    assert response.status_code == 302  # Redirect to login

def test_profile_page_no_bookings(transactional_db, client, user):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('account:profile'))
    assert response.status_code == 200
    assert 'You have no bookings yet' in response.content.decode()

# --- Edit Booking Tests ---
def test_edit_booking_authenticated_owner(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('account:edit_booking', args=[booking.pk]))
    assert response.status_code == 200
    assert 'Edit Booking' in response.content.decode()

def test_edit_booking_authenticated_not_owner(transactional_db, client, other_user, booking):
    client.login(email='other@example.com', password='testpass123')
    response = client.get(reverse('account:edit_booking', args=[booking.pk]))
    assert response.status_code == 404  # Should not be accessible

def test_edit_booking_unauthenticated(transactional_db, client, booking):
    response = client.get(reverse('account:edit_booking', args=[booking.pk]))
    assert response.status_code == 302  # Redirect to login

def test_edit_booking_success(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    new_date = (timezone.now().date() + timedelta(days=2)).strftime('%Y-%m-%d')
    data = {
        'session_date': new_date,
        'session_time': '15:00',
        'notes': 'Updated booking'
    }
    response = client.post(reverse('account:edit_booking', args=[booking.pk]), data)
    assert response.status_code == 302  # Redirect to profile
    booking.refresh_from_db()
    assert booking.session_date.strftime('%Y-%m-%d') == new_date
    assert booking.session_time == time(15, 0)
    assert booking.notes == 'Updated booking'

def test_edit_booking_duplicate_time(transactional_db, client, user, product):
    # Create two bookings for the same time
    tomorrow = timezone.now().date() + timedelta(days=1)
    booking1 = Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(14, 0),
        notes='First booking'
    )
    booking2 = Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(15, 0),
        notes='Second booking'
    )
    client.login(email='test@example.com', password='testpass123')
    # Try to edit booking2 to the same time as booking1
    data = {
        'session_date': tomorrow.strftime('%Y-%m-%d'),
        'session_time': '14:00',
        'notes': 'Updated booking'
    }
    response = client.post(reverse('account:edit_booking', args=[booking2.pk]), data)
    assert response.status_code == 200  # Form errors, stay on page
    assert 'already booked' in response.content.decode()

def test_edit_booking_past_date(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    yesterday = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    data = {
        'session_date': yesterday,
        'session_time': '15:00',
        'notes': 'Updated booking'
    }
    response = client.post(reverse('account:edit_booking', args=[booking.pk]), data)
    assert response.status_code == 200  # Form errors, stay on page
    assert 'cannot be in the past' in response.content.decode()

# --- Cancel Booking Tests ---
def test_cancel_booking_authenticated_owner(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 200
    assert 'Cancel Booking' in response.content.decode()
    assert '60-Minute Session' in response.content.decode()

def test_cancel_booking_authenticated_not_owner(transactional_db, client, other_user, booking):
    client.login(email='other@example.com', password='testpass123')
    response = client.get(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 404  # Should not be accessible

def test_cancel_booking_unauthenticated(transactional_db, client, booking):
    response = client.get(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 302  # Redirect to login

def test_cancel_booking_success(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.post(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 302  # Redirect to profile
    assert not Booking.objects.filter(pk=booking.pk).exists()

# --- Success Messages Tests ---
def test_edit_booking_success_message(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    new_date = (timezone.now().date() + timedelta(days=2)).strftime('%Y-%m-%d')
    data = {
        'session_date': new_date,
        'session_time': '15:00',
        'notes': 'Updated booking'
    }
    response = client.post(reverse('account:edit_booking', args=[booking.pk]), data)
    assert response.status_code == 302
    # Follow the redirect to check for success message
    response = client.get(reverse('account:profile'))
    assert 'Your booking has been updated successfully!' in response.content.decode()

def test_cancel_booking_success_message(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.post(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 302
    # Follow the redirect to check for success message
    response = client.get(reverse('account:profile'))
    assert 'Your booking has been cancelled successfully!' in response.content.decode()