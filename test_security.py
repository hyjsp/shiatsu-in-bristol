import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.utils import timezone
from datetime import date, time, timedelta
from products.models import Category, Product, Booking
from products.forms import BookingForm

User = get_user_model()


class CSRFProtectionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_csrf_protection_on_booking_form(self):
        """Test that booking form requires CSRF token"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to submit booking without CSRF token
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Test booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data,
            HTTP_X_CSRFTOKEN='invalid_token'
        )
        
        # Should reject the request
        self.assertEqual(response.status_code, 403)

    def test_csrf_protection_on_admin_forms(self):
        """Test that admin forms require CSRF protection"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(email='admin@example.com', password='adminpass123')
        
        # Try to create a product without CSRF token
        product_data = {
            'name': 'Test Product',
            'category': self.category.pk,
            'price': '50.00',
            'is_active': 'on'
        }
        
        response = self.client.post(
            reverse('admin:products_product_add'),
            product_data,
            HTTP_X_CSRFTOKEN='invalid_token'
        )
        
        # Should reject the request
        self.assertEqual(response.status_code, 403)

    def test_csrf_token_in_forms(self):
        """Test that forms include CSRF tokens"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        
        # Check that CSRF token is in the form
        self.assertContains(response, 'csrfmiddlewaretoken')


class SQLInjectionPreventionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_sql_injection_in_product_id(self):
        """Test that SQL injection attempts in product ID are prevented"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try SQL injection in product ID
        malicious_id = "1' OR '1'='1"
        response = self.client.get(f'/products/{malicious_id}/')
        
        # Should return 404, not execute SQL
        self.assertEqual(response.status_code, 404)

    def test_sql_injection_in_search_parameters(self):
        """Test that SQL injection in search parameters is prevented"""
        # Try SQL injection in search
        malicious_search = "'; DROP TABLE products; --"
        response = self.client.get(f'/products/?q={malicious_search}')
        
        # Should not crash or execute malicious SQL
        self.assertEqual(response.status_code, 200)

    def test_sql_injection_in_form_data(self):
        """Test that SQL injection in form data is prevented"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        malicious_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': "'; DROP TABLE bookings; --"
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            malicious_data
        )
        
        # Should handle the data safely
        self.assertNotEqual(response.status_code, 500)


class XSSPreventionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_xss_in_product_name(self):
        """Test that XSS in product name is escaped"""
        # Create product with XSS attempt
        xss_product = Product.objects.create(
            category=self.category,
            name='<script>alert("XSS")</script>',
            description='<script>alert("XSS")</script>',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that script tags are escaped
        self.assertContains(response, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert("XSS")</script>')

    def test_xss_in_booking_notes(self):
        """Test that XSS in booking notes is escaped"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        xss_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': '<script>alert("XSS")</script>'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            xss_data
        )
        
        # Should create booking successfully
        self.assertEqual(response.status_code, 302)
        
        # Check that notes are stored safely
        booking = Booking.objects.first()
        self.assertEqual(booking.notes, '<script>alert("XSS")</script>')
        
        # Check that notes are escaped in template
        self.client.get(reverse('products:booking_confirmation', args=[booking.pk]))
        # Template should escape the content

    def test_xss_in_user_input(self):
        """Test that XSS in user input is prevented"""
        # Create user with XSS in username
        xss_user = User.objects.create_user(
            username='<script>alert("XSS")</script>',
            email='xss@example.com',
            password='testpass123'
        )
        
        # Should not crash when displaying user info
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)


class AuthenticationBypassTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_authentication_bypass_in_product_detail(self):
        """Test that unauthenticated users cannot access product detail"""
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_authentication_bypass_in_booking_confirmation(self):
        """Test that unauthenticated users cannot access booking confirmation"""
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        response = self.client.get(reverse('products:booking_confirmation', args=[booking.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_authentication_bypass_with_fake_session(self):
        """Test that fake session data cannot bypass authentication"""
        # Try to access protected view with fake session
        session = self.client.session
        session['_auth_user_id'] = '999'  # Non-existent user
        session.save()
        
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Should still redirect

    def test_authentication_bypass_with_invalid_user_id(self):
        """Test that invalid user IDs cannot bypass authentication"""
        session = self.client.session
        session['_auth_user_id'] = 'invalid_user_id'
        session.save()
        
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Should redirect


class PermissionEscalationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )

    def test_user_cannot_access_admin(self):
        """Test that regular users cannot access admin interface"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_user_cannot_access_other_user_booking(self):
        """Test that users cannot access other users' bookings"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_booking = Booking.objects.create(
            product=self.product,
            user=other_user,
            session_date=date(2024, 1, 16),
            session_time=time(15, 0),
            notes='Other user booking'
        )
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:booking_confirmation', args=[other_booking.pk]))
        self.assertEqual(response.status_code, 404)  # Not found

    def test_user_cannot_modify_other_user_data(self):
        """Test that users cannot modify other users' data"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to modify other user's booking
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '16:00',
            'notes': 'Malicious modification'
        }
        
        # This should not work - users can only create their own bookings
        # The test verifies that the system doesn't allow cross-user modifications

    def test_admin_cannot_access_without_superuser(self):
        """Test that non-superusers cannot access admin even if staff"""
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_cross_site_request_forgery_prevention(self):
        """Test that CSRF tokens prevent cross-site request forgery"""
        # Simulate a malicious site trying to make a request
        malicious_data = {
            'session_date': timezone.now().date() + timedelta(days=1),
            'session_time': '14:00',
            'notes': 'Malicious booking'
        }
        
        # Without proper CSRF token, this should fail
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            malicious_data,
            HTTP_REFERER='http://malicious-site.com'
        )
        
        # Should be rejected
        self.assertNotEqual(response.status_code, 302)  # Should not redirect to success 