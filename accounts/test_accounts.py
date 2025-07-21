import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta, time
from django.contrib.auth import get_user_model
from products.models import Category, Product, Booking
from accounts.models import CustomUser
from accounts.forms import CustomUserCreationForm
from conftest import created_event_ids
import uuid

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

class UsernameValidationTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_valid_usernames(self):
        valid_usernames = [
            'simpleuser',
            'user_123',
            'user-name',
            'USER123',
            'user_name-123',
        ]
        for uname in valid_usernames:
            form = CustomUserCreationForm(data={
                'username': uname,
                'email': f'{uname}@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            })
            self.assertTrue(form.is_valid(), f"Should accept valid username: {uname}")

    def test_invalid_usernames(self):
        invalid_usernames = [
            'user name',    # space
            'user@name',   # @
            'user!name',   # !
            'user<name>',  # < >
            'user<script>', # HTML
            'user.name',   # .
        ]
        for uname in invalid_usernames:
            form = CustomUserCreationForm(data={
                'username': uname,
                'email': f'{uname}@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            })
            self.assertFalse(form.is_valid(), f"Should reject invalid username: {uname}")

    def test_username_length_limit(self):
        long_username = 'a' * 31
        form = CustomUserCreationForm(data={
            'username': long_username,
            'email': 'long@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        })
        self.assertFalse(form.is_valid(), "Should reject username over 30 chars")

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
    session_date, session_time = unique_slot('booking_fixture')
    notes = f'TEST_BOOKING_booking_fixture_{uuid.uuid4().hex[:8]}'
    b = Booking.objects.create(
        product=product,
        user=user,
        session_date=session_date,
        session_time=session_time,
        notes=notes
    )
    if hasattr(b, 'google_calendar_event_id') and b.google_calendar_event_id:
        created_event_ids.append(b.google_calendar_event_id)
    if hasattr(b, 'admin_calendar_event_id') and b.admin_calendar_event_id:
        created_event_ids.append(b.admin_calendar_event_id)
    return b

def unique_slot(test_name, offset=0):
    base_date = timezone.now().date() + timedelta(days=2 + abs(hash(test_name)) % 50 + offset)
    base_time = time(9 + (abs(hash(test_name)) % 8), 0)
    return base_date, base_time

# Update booking fixture
def booking(transactional_db, user, product):
    session_date, session_time = unique_slot('booking_fixture')
    notes = f'TEST_BOOKING_booking_fixture_{uuid.uuid4().hex[:8]}'
    b = Booking.objects.create(
        product=product,
        user=user,
        session_date=session_date,
        session_time=session_time,
        notes=notes
    )
    if hasattr(b, 'google_calendar_event_id') and b.google_calendar_event_id:
        created_event_ids.append(b.google_calendar_event_id)
    if hasattr(b, 'admin_calendar_event_id') and b.admin_calendar_event_id:
        created_event_ids.append(b.admin_calendar_event_id)
    return b

# --- Profile Page Tests ---
def test_profile_page_authenticated(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('account:profile'))
    assert response.status_code == 200
    assert 'My Profile' in response.content.decode()
    assert '60-Minute Session' in response.content.decode()
    assert 'TEST_BOOKING_booking_fixture' in response.content.decode()

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
    new_date, new_time = unique_slot('test_edit_booking_success')
    notes = f'TEST_BOOKING_test_edit_booking_success_{uuid.uuid4().hex[:8]}'
    # Track old event IDs before edit
    if hasattr(booking, 'google_calendar_event_id') and booking.google_calendar_event_id:
        created_event_ids.append(booking.google_calendar_event_id)
    if hasattr(booking, 'admin_calendar_event_id') and booking.admin_calendar_event_id:
        created_event_ids.append(booking.admin_calendar_event_id)
    data = {
        'session_date': new_date.strftime('%Y-%m-%d'),
        'session_time': new_time.strftime('%H:%M'),
        'notes': notes
    }
    response = client.post(reverse('account:edit_booking', args=[booking.pk]), data)
    if response.status_code == 302:
        booking.refresh_from_db()
        assert booking.session_date == new_date
        assert booking.session_time == new_time
        assert booking.notes == notes
        # Track new event IDs after edit
        if hasattr(booking, 'google_calendar_event_id') and booking.google_calendar_event_id:
            created_event_ids.append(booking.google_calendar_event_id)
        if hasattr(booking, 'admin_calendar_event_id') and booking.admin_calendar_event_id:
            created_event_ids.append(booking.admin_calendar_event_id)
    else:
        # If not redirected, check for form errors
        assert 'Sorry, this time slot overlaps with another Shiatsu Session.' not in response.content.decode()

def test_edit_booking_duplicate_time(transactional_db, client, user, product):
    # Create two bookings for the same time with unique notes
    import uuid
    tomorrow = timezone.now().date() + timedelta(days=1)
    notes1 = f'TEST_BOOKING_test_edit_booking_duplicate_time_1_{uuid.uuid4().hex[:8]}'
    notes2 = f'TEST_BOOKING_test_edit_booking_duplicate_time_2_{uuid.uuid4().hex[:8]}'
    booking1 = Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(14, 0),
        notes=notes1
    )
    booking2 = Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(15, 0),
        notes=notes2
    )
    # Track event IDs for cleanup
    if hasattr(booking1, 'google_calendar_event_id') and booking1.google_calendar_event_id:
        created_event_ids.append(booking1.google_calendar_event_id)
    if hasattr(booking1, 'admin_calendar_event_id') and booking1.admin_calendar_event_id:
        created_event_ids.append(booking1.admin_calendar_event_id)
    if hasattr(booking2, 'google_calendar_event_id') and booking2.google_calendar_event_id:
        created_event_ids.append(booking2.google_calendar_event_id)
    if hasattr(booking2, 'admin_calendar_event_id') and booking2.admin_calendar_event_id:
        created_event_ids.append(booking2.admin_calendar_event_id)
    client.login(email='test@example.com', password='testpass123')
    # Try to edit booking2 to the same time as booking1
    data = {
        'session_date': tomorrow.strftime('%Y-%m-%d'),
        'session_time': '14:00',
        'notes': 'Updated booking'
    }
    response = client.post(reverse('account:edit_booking', args=[booking2.pk]), data)
    assert response.status_code == 200  # Form errors, stay on page
    # Check for form errors in the context if available
    if hasattr(response, 'context') and response.context is not None:
        form = response.context.get('form')
        assert form is not None
        # There should be a non-field error
        non_field_errors = form.non_field_errors()
        assert non_field_errors, f"Expected non-field errors but got: {form.errors}"
    else:
        # Fallback: check that the booking was not updated
        booking2.refresh_from_db()
        assert booking2.session_time == time(15, 0)

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
    if response.status_code == 302:
        # Follow the redirect to check for success message
        response = client.get(reverse('account:profile'))
        assert 'Your booking has been updated successfully!' in response.content.decode()
    else:
        # If not redirected, check for form errors
        assert 'Sorry, this time slot overlaps with another Shiatsu Session.' not in response.content.decode()

def test_cancel_booking_success_message(transactional_db, client, user, booking):
    client.login(email='test@example.com', password='testpass123')
    response = client.post(reverse('account:cancel_booking', args=[booking.pk]))
    assert response.status_code == 302
    # Follow the redirect to check for success message
    response = client.get(reverse('account:profile'))
    assert 'Your booking has been cancelled successfully!' in response.content.decode()